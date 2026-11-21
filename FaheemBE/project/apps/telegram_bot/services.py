import os
import requests
import hashlib
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
from django.conf import settings
from django.utils import timezone
from .models import TelegramUser, InteractionLog, StudentClaimRequest, ClaimStatus, UserRole
from .selectors import get_or_create_telegram_user
from apps.academic.selectors import get_student_current_grades, get_yearly_identity
from apps.academic.models import AcademicRecord, YearlyExamIdentity, Course
from apps.drive_sync.selectors import get_materials_by_year_and_category
from apps.drive_sync.services import GoogleDriveService
from apps.drive_sync.models import DriveFile, EducationalMaterial, SourceRevision
from apps.ingestion.models import ProcessingJob, JobState
from apps.ingestion.services import IngestionPipelineService

logger = logging.getLogger(__name__)


class TelegramBotService:
    """
    خدمة محرك بوت تليغرام التفاعلية الكاملة:
    - التحقق من الـ Idempotency ومعالجة الـ Webhooks / Polling.
    - إدارة جلسات الطلاب (عرض العلامات، تصفح المواد التعليمية، وربط السجلات).
    - معالج الرفع التفاعلي الذكي (Conversation / Wizard Flow) للمشرفين والمحتوى.
    - التكامل المباشر مع Google Drive لحساب بصمة الملفات (SHA-256) وفهرستها فورياً.
    """

    API_BASE = "https://api.telegram.org/bot"

    def __init__(self):
        self.token = settings.FAHEEM_CONFIG.get('TELEGRAM_BOT_TOKEN', '')
        self.url = f"{self.API_BASE}{self.token}" if self.token else ""

    def send_message(self, chat_id: int, text: str, reply_markup: Optional[Dict[str, Any]] = None) -> bool:
        """إرسال رسالة نصية عبر تليغرام."""
        if not self.url:
            logger.warning("Telegram Bot Token is not set.")
            return False

        payload = {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'Markdown'
        }
        if reply_markup:
            payload['reply_markup'] = reply_markup

        try:
            resp = requests.post(f"{self.url}/sendMessage", json=payload, timeout=15)
            return resp.status_code == 200
        except Exception as e:
            logger.error(f"Error sending message to {chat_id}: {e}")
            return False

    def download_telegram_file(self, file_id: str, target_path: Path) -> bool:
        """تنزيل ملف أرسله المستخدم عبر تليغرام إلى مسار محلي."""
        if not self.url:
            return False
        try:
            # 1. جلب مسار الملف من تليغرام
            r = requests.get(f"{self.url}/getFile", params={'file_id': file_id}, timeout=15)
            if r.status_code != 200:
                return False
            data = r.json()
            if not data.get('ok'):
                return False

            file_path = data['result']['file_path']
            download_url = f"https://api.telegram.org/file/bot{self.token}/{file_path}"

            # 2. تنزيل البايتات الفعلية
            target_path.parent.mkdir(parents=True, exist_ok=True)
            dl_resp = requests.get(download_url, stream=True, timeout=60)
            if dl_resp.status_code == 200:
                with open(target_path, 'wb') as f:
                    for chunk in dl_resp.iter_content(chunk_size=8192):
                        f.write(chunk)
                return True
        except Exception as ex:
            logger.error(f"Error downloading file {file_id}: {ex}")
        return False

    def handle_webhook_update(self, update: Dict[str, Any]) -> Dict[str, Any]:
        """معالجة التحديث الوارد من تليغرام بأسلوب Idempotent."""
        update_id = update.get('update_id')
        if not update_id:
            return {'status': 'ignored', 'reason': 'missing_update_id'}

        # معالجة الرسائل العادية أو المستندات
        if 'message' in update:
            msg = update['message']
            from_user = msg.get('from', {})
            chat_id = msg.get('chat', {}).get('id')
            text = msg.get('text', '').strip()
            doc = msg.get('document')

            tg_user, _ = get_or_create_telegram_user(
                telegram_id=from_user.get('id'),
                username=from_user.get('username'),
                first_name=from_user.get('first_name', ''),
                last_name=from_user.get('last_name', '')
            )

            # تسجيل التفاعل لمنع التكرار
            if InteractionLog.objects.filter(telegram_user=tg_user, update_id=update_id).exists():
                return {'status': 'duplicate_update'}

            # التحقق إن كان المستخدم في خضم معالج الرفع (Wizard)
            wizard_state = tg_user.active_wizard_state or {}
            step = wizard_state.get('step')

            # 1. إذا كان ينتظر إدخال كود المصادقة الخاص بالمشرفين
            if step == 'WAITING_ADMIN_CODE' and text:
                response_text = self._handle_admin_auth_code(tg_user, chat_id, text)

            # 2. إذا كان ينتظر إرسال ملفات للرفع
            elif step == 'WAITING_FILES':
                if text == '/done' or text == '/cancel':
                    tg_user.active_wizard_state = {}
                    tg_user.save(update_fields=['active_wizard_state'])
                    response_text = "✅ تم إنهاء جلسة الرفع بنجاح. أرسل /start للعودة للقائمة الرئيسية."
                    self.send_message(chat_id, response_text)
                elif doc:
                    response_text = self._process_uploaded_document(tg_user, chat_id, doc)
                else:
                    response_text = "📥 يرجى إرسال ملف (Document/PDF) لرفعه، أو كتابة /done للإنهاء."
                    self.send_message(chat_id, response_text)

            # 3. توجيه الأوامر والرسائل العادية
            else:
                response_text = self._route_command(tg_user, chat_id, text)

            InteractionLog.objects.create(
                telegram_user=tg_user,
                update_id=update_id,
                command=text.split()[0] if text else "DOCUMENT",
                payload=msg,
                response_text=response_text
            )

            return {'status': 'processed'}

        # معالجة نقرات الأزرار التفاعلية (Callback Query)
        elif 'callback_query' in update:
            cb = update['callback_query']
            from_user = cb.get('from', {})
            chat_id = cb.get('message', {}).get('chat', {}).get('id')
            data = cb.get('data', '')

            tg_user, _ = get_or_create_telegram_user(
                telegram_id=from_user.get('id'),
                username=from_user.get('username'),
                first_name=from_user.get('first_name', ''),
                last_name=from_user.get('last_name', '')
            )

            response_text = self._handle_callback(tg_user, chat_id, data)
            return {'status': 'callback_processed'}

        return {'status': 'unsupported_update_type'}

    def _route_command(self, tg_user: TelegramUser, chat_id: int, text: str) -> str:
        """توجيه الأوامر الرئيسية للرحلات المناسبة."""
        if text.startswith('/start'):
            # إلغاء أي جلسة رفع معلقة عند فتح القائمة الرئيسية
            tg_user.active_wizard_state = {}
            tg_user.save(update_fields=['active_wizard_state'])

            role_badge = "👑 مشرف معتمد" if tg_user.role == UserRole.ADMIN else ("✅ طالب موثق" if tg_user.is_verified else "زائر")
            msg = (
                f"👋 **أهلاً بك في منصة فهيم الرسمية**\n"
                f"كلية الهندسة المعلوماتية — جامعة دمشق 🎓\n"
                f"الصفة: **{role_badge}**\n\n"
                f"اختر الخدمة المطلوبة من القائمة أدناه:"
            )
            keyboard = {
                'inline_keyboard': [
                    [{'text': '📊 نتائجي وعلاماتي الرسمية', 'callback_data': 'cmd_results'}],
                    [{'text': '📚 مكتبة المحاضرات والمواد', 'callback_data': 'cmd_materials'}],
                    [{'text': '🔐 توثيق / ربط حسابي الأكاديمي', 'callback_data': 'cmd_claim'}],
                    [{'text': '📤 رفع وإدارة المحتوى (للمشرفين)', 'callback_data': 'cmd_wizard_start'}],
                ]
            }
            self.send_message(chat_id, msg, reply_markup=keyboard)
            return msg

        elif text.startswith('/upload') or text.startswith('/admin'):
            return self._start_admin_upload_wizard(tg_user, chat_id)

        elif text.startswith('/results'):
            return self._handle_results_request(tg_user, chat_id)

        elif text.startswith('/materials'):
            return self._handle_materials_request(chat_id)

        elif text.startswith('/claim'):
            parts = text.split()
            if len(parts) >= 2:
                exam_num = parts[1].strip()
                yearly_id = YearlyExamIdentity.objects.filter(exam_number=exam_num).select_related('academic_record').first()
                if yearly_id:
                    tg_user.linked_record = yearly_id.academic_record
                    tg_user.is_verified = True
                    tg_user.save(update_fields=['linked_record', 'is_verified'])
                    msg = (
                        f"🎉 **تم توثيق هويتك الأكاديمية بنجاح!**\n"
                        f"الطالب: **{yearly_id.academic_record.official_name}**\n"
                        f"الرقم الامتحاني: `{exam_num}`\n\n"
                        f"يمكنك الآن الضغط على زر 'نتائجي وعلاماتي الرسمية' للاطلاع على نتائجك."
                    )
                else:
                    msg = f"ℹ لم يتم العثور على سجل مسبق للرقم الامتحاني: `{exam_num}`.\nتم تسجيل طلبك للمراجعة."
            else:
                msg = "الصيغة الصحيحة:\n`/claim <الرقم_الامتحاني>`\nمثال: `/claim 12345`"
            self.send_message(chat_id, msg)
            return msg

        else:
            msg = "أمر غير معروف. استخدم /start للعودة للقائمة الرئيسية."
            self.send_message(chat_id, msg)
            return msg

    # ==========================================================
    # معالج الرفع التفاعلي للمشرفين (Conversation / Wizard Flow)
    # ==========================================================

    def _start_admin_upload_wizard(self, tg_user: TelegramUser, chat_id: int) -> str:
        """بدء معالج الرفع التفاعلي مع التحقق من الهوية والصلاحيات."""
        # 1. التحقق من صلاحية المشرف
        if tg_user.role != UserRole.ADMIN:
            tg_user.active_wizard_state = {'step': 'WAITING_ADMIN_CODE'}
            tg_user.save(update_fields=['active_wizard_state'])
            msg = (
                "🔐 **التحقق من صلاحيات المشرف (Authorization)**\n\n"
                "هذا المسار مخصص للمشرفين وممثلي المواد لرفع المحتوى والعلامات إلى Google Drive.\n"
                "يرجى إرسال **رمز/كود التحقق** الخاص بالمشرفين للمصادقة وتأكيد صلاحية حسابك:"
            )
            self.send_message(chat_id, msg)
            return msg

        # 2. في حال كان مشرفاً معتمداً مسبقاً، ننتقل مباشرة للخطوة (أ)
        return self._show_wizard_step_target(tg_user, chat_id)

    def _handle_admin_auth_code(self, tg_user: TelegramUser, chat_id: int, code_input: str) -> str:
        """التحقق من كود المصادقة وترقية المستخدم لمشرف."""
        expected_passcode = settings.FAHEEM_CONFIG.get('TELEGRAM_ADMIN_PASSCODE', 'FaheemAdmin2026')

        if code_input.strip() == expected_passcode.strip():
            tg_user.role = UserRole.ADMIN
            tg_user.is_verified = True
            tg_user.active_wizard_state = {}
            tg_user.save(update_fields=['role', 'is_verified', 'active_wizard_state'])

            self.send_message(chat_id, "✅ **تم التحقق من هويتك كمشرف بنجاح!** مرحباً بك في لوحة الرفع الذكية.")
            return self._show_wizard_step_target(tg_user, chat_id)
        else:
            msg = "❌ **كود التحقق غير صحيح.** الوصول مرفوض. أرسل /start للعودة."
            tg_user.active_wizard_state = {}
            tg_user.save(update_fields=['active_wizard_state'])
            self.send_message(chat_id, msg)
            return msg

    def _show_wizard_step_target(self, tg_user: TelegramUser, chat_id: int) -> str:
        """الخطوة (أ): تحديد ماذا يريد المستخدم أن يرفع."""
        tg_user.active_wizard_state = {'step': 'CHOOSE_TARGET', 'data': {}}
        tg_user.save(update_fields=['active_wizard_state'])

        msg = (
            "📤 **معالج رفع المحتوى إلى Google Drive**\n"
            "الخطوة 1: ماذا تريد أن ترفع؟\n\n"
            "اختر القسم المناسب من الخيارات أدناه:"
        )
        keyboard = {
            'inline_keyboard': [
                [{'text': '📊 علامات جامعية رسمية', 'callback_data': 'wz_tgt_marks'}],
                [{'text': '📚 مادة ومحاضرات دراسية', 'callback_data': 'wz_tgt_materials'}],
                [{'text': '📝 دورات وسلالم تصحيح وززنقة', 'callback_data': 'wz_tgt_exams'}],
                [{'text': '📢 إعلانات جامعية رسمية', 'callback_data': 'wz_tgt_announcements'}],
                [{'text': '🎓 مسودات قرارات التخرج', 'callback_data': 'wz_tgt_grad'}],
            ]
        }
        self.send_message(chat_id, msg, reply_markup=keyboard)
        return msg

    def _handle_callback(self, tg_user: TelegramUser, chat_id: int, data: str) -> str:
        """معالجة كافة نقرات الأزرار التفاعلية بما فيها مسار الرفع (Wizard)."""
        # الأوامر العامة
        if data == 'cmd_results':
            return self._handle_results_request(tg_user, chat_id)
        elif data == 'cmd_materials':
            return self._handle_materials_request(chat_id)
        elif data == 'cmd_claim':
            return self._handle_claim_prompt(tg_user, chat_id)
        elif data == 'cmd_wizard_start':
            return self._start_admin_upload_wizard(tg_user, chat_id)

        # استعراض المواد العادية للطلاب
        elif data.startswith('year_'):
            year_num = int(data.split('_')[1])
            msg = f"اختر التصنيف المطلوب لمواد السنة {year_num}:"
            categories = ['دورات', 'محاضرات', 'سلايدات', 'سلالم', 'زنقة', 'ملحق']
            keyboard = {
                'inline_keyboard': [
                    [{'text': f"📁 {cat}", 'callback_data': f"cat_{year_num}_{cat}"}]
                    for cat in categories
                ]
            }
            self.send_message(chat_id, msg, reply_markup=keyboard)
            return msg

        elif data.startswith('cat_'):
            _, year, cat = data.split('_', 2)
            materials = get_materials_by_year_and_category(study_year=int(year), category=cat)[:15]
            if not materials.exists():
                msg = f"لا توجد ملفات متوفرة حالياً في قسم ({cat}) للسنة {year}."
            else:
                lines = [f"📚 **مجلدات ومواد {cat} — السنة {year}:**\n"]
                for m in materials:
                    link = f" [🔗 فتح في درايف]({m.drive_file.web_view_link})" if m.drive_file.web_view_link else ""
                    lines.append(f"• **{m.course_name}**:{link}")
                msg = "\n".join(lines)
            self.send_message(chat_id, msg)
            return msg

        # ==========================================
        # خطوات معالج الرفع (Wizard Callback Steps)
        # ==========================================
        wz_state = tg_user.active_wizard_state or {}
        wz_data = wz_state.get('data', {})

        # الخطوة أ: تحديد نوع المحتوى
        if data.startswith('wz_tgt_'):
            target_key = data.replace('wz_tgt_', '')

            if target_key == 'marks':
                wz_data.update({
                    'target_type': 'marks',
                    'target_folder_id': '1pQ2NKAz2NvXA5iwGekYbvh_NeUeTV7eF',
                    'path_label': 'علامات جامعية'
                })
                return self._show_wizard_step_upload_mode(tg_user, chat_id, wz_data)

            elif target_key == 'announcements':
                wz_data.update({
                    'target_type': 'announcements',
                    'target_folder_id': '19C0FBFqeT8b2KJWXue8tWQml6LwR7WWL',
                    'path_label': 'اعلانات جامعية'
                })
                return self._show_wizard_step_upload_mode(tg_user, chat_id, wz_data)

            elif target_key == 'grad':
                wz_data.update({
                    'target_type': 'grad',
                    'target_folder_id': '1GHmIVWwH-J4SiFe58dbc8UIFZDRfIcOo',
                    'path_label': 'مسودات قرارات التخرج'
                })
                return self._show_wizard_step_upload_mode(tg_user, chat_id, wz_data)

            elif target_key in ['materials', 'exams']:
                wz_data['target_type'] = target_key
                wz_state['data'] = wz_data
                wz_state['step'] = 'CHOOSE_YEAR'
                tg_user.active_wizard_state = wz_state
                tg_user.save(update_fields=['active_wizard_state'])

                msg = "📂 **الخطوة 2: اختر السنة الدراسية للمقرر:**"
                keyboard = {
                    'inline_keyboard': [
                        [{'text': 'سنة اولى 1️⃣', 'callback_data': 'wz_yr_1'}, {'text': 'سنة ثانية 2️⃣', 'callback_data': 'wz_yr_2'}],
                        [{'text': 'سنة ثالثة 3️⃣', 'callback_data': 'wz_yr_3'}, {'text': 'سنة رابعة 4️⃣', 'callback_data': 'wz_yr_4'}],
                        [{'text': 'سنة خامسة 5️⃣', 'callback_data': 'wz_yr_5'}],
                    ]
                }
                self.send_message(chat_id, msg, reply_markup=keyboard)
                return msg

        # الخطوة ب-1: اختيار السنة
        elif data.startswith('wz_yr_'):
            year_num = int(data.replace('wz_yr_', ''))
            year_names = {1: 'سنة اولى', 2: 'سنة ثانية', 3: 'سنة ثالثة', 4: 'سنة رابعة', 5: 'سنة خامسة'}
            wz_data['study_year'] = year_num
            wz_data['study_year_label'] = year_names.get(year_num, 'سنة اولى')

            wz_state['data'] = wz_data
            wz_state['step'] = 'CHOOSE_SEMESTER'
            tg_user.active_wizard_state = wz_state
            tg_user.save(update_fields=['active_wizard_state'])

            msg = f"🗓️ **الخطوة 3 ({wz_data['study_year_label']}): اختر الفصل الدراسي:**"
            keyboard = {
                'inline_keyboard': [
                    [{'text': 'الفصل الأول 🍂', 'callback_data': 'wz_sem_1'}, {'text': 'الفصل الثاني 🌸', 'callback_data': 'wz_sem_2'}],
                ]
            }
            self.send_message(chat_id, msg, reply_markup=keyboard)
            return msg

        # الخطوة ب-2: اختيار الفصل
        elif data.startswith('wz_sem_'):
            sem_num = int(data.replace('wz_sem_', ''))
            wz_data['semester'] = sem_num
            year_num = wz_data.get('study_year', 1)

            # إذا كانت السنة رابعة أو خامسة -> نطلب الاختصاص
            if year_num in [4, 5]:
                wz_state['data'] = wz_data
                wz_state['step'] = 'CHOOSE_DEPT'
                tg_user.active_wizard_state = wz_state
                tg_user.save(update_fields=['active_wizard_state'])

                msg = "🏢 **الخطوة 4: اختر التخصص الأكاديمي:**"
                keyboard = {
                    'inline_keyboard': [
                        [{'text': 'هندسة البرمجيات 💻', 'callback_data': 'wz_dpt_برمجيات'}],
                        [{'text': 'الذكاء الصنعي 🤖', 'callback_data': 'wz_dpt_ذكاء'}],
                        [{'text': 'الشبكات الحاسوبية 🌐', 'callback_data': 'wz_dpt_شبكات'}],
                    ]
                }
                self.send_message(chat_id, msg, reply_markup=keyboard)
                return msg
            else:
                wz_data['department'] = 'عام'
                return self._show_wizard_step_courses(tg_user, chat_id, wz_data)

        # الخطوة ب-3: اختيار الاختصاص
        elif data.startswith('wz_dpt_'):
            dept = data.replace('wz_dpt_', '')
            wz_data['department'] = dept
            return self._show_wizard_step_courses(tg_user, chat_id, wz_data)

        # الخطوة ب-4: اختيار المقرر المحدد
        elif data.startswith('wz_crs_'):
            course_id = int(data.replace('wz_crs_', ''))
            course = Course.objects.filter(id=course_id).first()
            if not course:
                self.send_message(chat_id, "مقرر غير موجود.")
                return ""

            wz_data['course_id'] = course.id
            wz_data['course_name'] = course.name

            # عرض المجلدات الفرعية الستة للمادة
            wz_state['data'] = wz_data
            wz_state['step'] = 'CHOOSE_CATEGORY'
            tg_user.active_wizard_state = wz_state
            tg_user.save(update_fields=['active_wizard_state'])

            msg = f"📁 **اختر المجلد الفرعي داخل مقرر ({course.name}):**"
            categories = ['محاضرات', 'سلايدات', 'دورات', 'سلالم', 'زنقة', 'ملحق']
            keyboard = {
                'inline_keyboard': [
                    [{'text': f"📂 {cat}", 'callback_data': f"wz_cat_{cat}"}]
                    for cat in categories
                ]
            }
            self.send_message(chat_id, msg, reply_markup=keyboard)
            return msg

        # الخطوة ب-5: اختيار المجلد الفرعي وتحديد المسار في Google Drive
        elif data.startswith('wz_cat_'):
            category = data.replace('wz_cat_', '')
            wz_data['category'] = category

            # حل أو إنشاء المجلد على درايف تلقائياً
            drive_svc = GoogleDriveService()
            dest_folder_id = '1day7zXkkzfyu768Xao8yLKHuDGMzbYgC'  # افتراضي مجلد المواد
            if drive_svc.is_configured():
                try:
                    dest_folder_id = drive_svc.get_or_create_course_material_folder(
                        study_year_label=wz_data.get('study_year_label', 'سنة اولى'),
                        department_label=wz_data.get('department', 'عام'),
                        course_name=wz_data.get('course_name', 'مقرر'),
                        category=category
                    )
                except Exception as ex:
                    logger.error(f"Error resolving drive folder: {ex}")

            wz_data['target_folder_id'] = dest_folder_id
            wz_data['path_label'] = f"{wz_data.get('study_year_label')} -> {wz_data.get('department')} -> {wz_data.get('course_name')} -> {category}"

            return self._show_wizard_step_upload_mode(tg_user, chat_id, wz_data)

        # الخطوة (ج): تحديد نوع الرفع (Single vs Bulk)
        elif data in ['wz_mode_single', 'wz_mode_bulk']:
            upload_mode = 'single' if data == 'wz_mode_single' else 'bulk'
            wz_data['upload_mode'] = upload_mode
            wz_data['uploaded_files_count'] = 0

            wz_state['data'] = wz_data
            wz_state['step'] = 'WAITING_FILES'
            tg_user.active_wizard_state = wz_state
            tg_user.save(update_fields=['active_wizard_state'])

            mode_text = "ملف واحد فقط (Single File)" if upload_mode == 'single' else "حزمة ملفات متعددة (Bulk Upload)"
            msg = (
                f"📥 **جاهز لاستقبال الملفات الآن!**\n\n"
                f"📁 **المسار المستهدف على Google Drive:**\n"
                f"`{wz_data.get('path_label')}`\n\n"
                f"⚙️ **نمط الرفع:** {mode_text}\n\n"
                f"👇 أرسل ملف الـ PDF أو المستند المطلوب رفعه عبر المحادثة الآن:"
            )
            self.send_message(chat_id, msg)
            return msg

        return ""

    def _show_wizard_step_courses(self, tg_user: TelegramUser, chat_id: int, wz_data: Dict[str, Any]) -> str:
        """عرض المقررات المتاحة المطابقة للسنة والفصل والتخصص."""
        year_num = wz_data.get('study_year', 1)
        sem_num = wz_data.get('semester', 1)
        dept = wz_data.get('department', 'عام')

        courses = Course.objects.filter(
            original_study_year=year_num,
            department=dept
        ).order_by('name')

        if not courses.exists():
            courses = Course.objects.filter(original_study_year=year_num).order_by('name')

        wz_state = tg_user.active_wizard_state or {}
        wz_state['data'] = wz_data
        wz_state['step'] = 'CHOOSE_COURSE'
        tg_user.active_wizard_state = wz_state
        tg_user.save(update_fields=['active_wizard_state'])

        msg = f"📖 **اختر المقرر الدراسي ({wz_data.get('study_year_label')} - {dept}):**"
        keyboard_buttons = []
        for c in courses[:20]:
            keyboard_buttons.append([{'text': f"📘 {c.name}", 'callback_data': f"wz_crs_{c.id}"}])

        keyboard = {'inline_keyboard': keyboard_buttons}
        self.send_message(chat_id, msg, reply_markup=keyboard)
        return msg

    def _show_wizard_step_upload_mode(self, tg_user: TelegramUser, chat_id: int, wz_data: Dict[str, Any]) -> str:
        """الخطوة (ج): سؤال تحديد نوع الرفع: هل ترفع ملفاً واحداً أم حزمة متعددة؟"""
        wz_state = tg_user.active_wizard_state or {}
        wz_state['data'] = wz_data
        wz_state['step'] = 'CHOOSE_UPLOAD_MODE'
        tg_user.active_wizard_state = wz_state
        tg_user.save(update_fields=['active_wizard_state'])

        msg = (
            f"📍 **المسار المحدد:** `{wz_data.get('path_label')}`\n\n"
            f"❓ **ما هو نوع الرفع المطلوب؟**"
        )
        keyboard = {
            'inline_keyboard': [
                [{'text': '📄 ملف واحد فقط (Single File)', 'callback_data': 'wz_mode_single'}],
                [{'text': '📦 حزمة ملفات متعددة (Bulk Upload)', 'callback_data': 'wz_mode_bulk'}],
            ]
        }
        self.send_message(chat_id, msg, reply_markup=keyboard)
        return msg

    def _process_uploaded_document(self, tg_user: TelegramUser, chat_id: int, doc: Dict[str, Any]) -> str:
        """
        الخطوة (د): استلام الملف من تليغرام، حساب بصمته، رفعه إلى Google Drive وفهرسته.
        """
        file_id = doc.get('file_id')
        file_name = doc.get('file_name', 'document.pdf')
        mime_type = doc.get('mime_type', 'application/pdf')
        file_size = doc.get('file_size', 0)

        wz_state = tg_user.active_wizard_state or {}
        wz_data = wz_state.get('data', {})
        target_folder_id = wz_data.get('target_folder_id')
        path_label = wz_data.get('path_label', 'Google Drive')
        upload_mode = wz_data.get('upload_mode', 'single')

        self.send_message(chat_id, f"⏳ جارٍ تنزيل وحساب بصمة `{file_name}` ورفعه إلى Google Drive...")

        staging_dir = Path(settings.BASE_DIR) / 'media' / 'staging' / 'wizard_uploads'
        staging_dir.mkdir(parents=True, exist_ok=True)
        temp_path = staging_dir / f"tg_{tg_user.telegram_id}_{file_name}"

        # 1. تنزيل الملف من تليغرام
        dl_success = self.download_telegram_file(file_id, temp_path)
        if not dl_success:
            err_msg = f"❌ تعذر تنزيل الملف `{file_name}` من سيرفرات تليغرام."
            self.send_message(chat_id, err_msg)
            return err_msg

        # 2. حساب بصمة SHA-256
        hasher = hashlib.sha256()
        with open(temp_path, 'rb') as f:
            while chunk := f.read(8192):
                hasher.update(chunk)
        digest = hasher.hexdigest()

        # 3. الرفع الفعلي إلى Google Drive
        drive_svc = GoogleDriveService()
        uploaded_id = f"tg_{digest[:12]}"
        web_link = None

        if drive_svc.is_configured() and target_folder_id:
            try:
                up_res = drive_svc.upload_file(
                    local_path=temp_path,
                    parent_folder_id=target_folder_id,
                    file_name=file_name,
                    mime_type=mime_type
                )
                uploaded_id = up_res.get('id', uploaded_id)
                web_link = up_res.get('webViewLink')
            except Exception as e:
                logger.error(f"Error uploading to drive: {e}")

        # 4. تسجيل الملف في قاعدة البيانات
        drive_file, _ = DriveFile.objects.update_or_create(
            drive_file_id=uploaded_id,
            defaults={
                'name': file_name,
                'mime_type': mime_type,
                'parent_folder_id': target_folder_id,
                'drive_path': path_label,
                'web_view_link': web_link,
                'active': True
            }
        )

        # إذا كان المرفوع مادة دراسية -> نسجلها في EducationalMaterial
        if wz_data.get('course_name'):
            EducationalMaterial.objects.update_or_create(
                drive_file=drive_file,
                defaults={
                    'study_year': wz_data.get('study_year', 1),
                    'department': wz_data.get('department', 'عام'),
                    'course_name': wz_data.get('course_name'),
                    'category': wz_data.get('category', 'محاضرات'),
                    'title': file_name.replace('.pdf', ''),
                    'is_published': True
                }
            )

        # إذا كان المرفوع علامات امتحانية -> ندخله في خط Ingestion Pipeline فورياً
        if wz_data.get('target_type') == 'marks' and mime_type == 'application/pdf':
            rev = SourceRevision.objects.create(
                drive_file=drive_file,
                pdf_digest=digest,
                snapshot_ref=str(temp_path),
                file_size_bytes=file_size
            )
            job = ProcessingJob.objects.create(
                source_revision=rev,
                state=JobState.PENDING,
                correlation_id=f"tg_upload_{digest[:10]}",
                requested_by=f"TG_ADMIN_{tg_user.telegram_id}"
            )
            IngestionPipelineService.execute_job(job)

        # 5. تنظيف الملف المؤقت
        if temp_path.exists():
            temp_path.unlink()

        # 6. الرد بنتيجة العملية
        count = wz_data.get('uploaded_files_count', 0) + 1
        wz_data['uploaded_files_count'] = count
        wz_state['data'] = wz_data

        drive_btn = f"\n🔗 [عرض الملف في Google Drive]({web_link})" if web_link else ""
        success_msg = (
            f"✅ **تم رفع وتوثيق الملف بنجاح!**\n\n"
            f"📄 **اسم الملف:** `{file_name}`\n"
            f"📁 **المجلد:** `{path_label}`\n"
            f"🔒 **بصمة SHA-256:** `{digest[:20]}...`{drive_btn}\n"
        )

        if upload_mode == 'single':
            tg_user.active_wizard_state = {}
            tg_user.save(update_fields=['active_wizard_state'])
            success_msg += "\n🎉 **اكتملت العملية بنجاح.** أرسل /start للعودة للقائمة الرئيسية."
        else:
            tg_user.active_wizard_state = wz_state
            tg_user.save(update_fields=['active_wizard_state'])
            success_msg += f"\n📦 إجمالي الملفات المرفوعة في هذه الجلسة: **{count}**\nأرسل الملف التالي، أو اكتب **/done** للإنهاء."

        self.send_message(chat_id, success_msg)
        return success_msg

    # ==========================================================
    # خدمات الاستعلام العامة للطلاب
    # ==========================================================

    def _handle_results_request(self, tg_user: TelegramUser, chat_id: int) -> str:
        """عرض العلامات الرسمية المعتمدة للطالب."""
        if not tg_user.is_verified or not tg_user.linked_record:
            msg = (
                "⚠️ **حسابك غير مرتبط بسجل أكاديمي موثق بعد.**\n\n"
                "لعرض درجاتك الرسمية، يرجى ربط حسابك برقمك الامتحاني عبر الضغط على: **ربط حسابي الأكاديمي** أو كتابة:\n"
                "`/claim <رقم_الامتحان>`"
            )
            keyboard = {
                'inline_keyboard': [
                    [{'text': '🔐 توثيق وربط الحساب الآن', 'callback_data': 'cmd_claim'}]
                ]
            }
            self.send_message(chat_id, msg, reply_markup=keyboard)
            return msg

        grades = get_student_current_grades(record_id=tg_user.linked_record_id)
        if not grades.exists():
            msg = (
                f"ℹ الطالب: **{tg_user.linked_record.official_name}**\n\n"
                f"لا توجد نتائج أو علامات رسمية منشورة لك حتى الآن في قاعدة البيانات."
            )
            self.send_message(chat_id, msg)
            return msg

        lines = [f"📊 **النتائج والعلامات الرسمية المعتمدة:**\nالطالب: **{tg_user.linked_record.official_name}**\n"]
        for g in grades:
            status_text = f"**{g.final_mark}**" if g.final_mark is not None else f"غائب ({g.absence_reason})"
            lines.append(f"• **{g.scope.course.name}** ({g.scope.exam_session.label}): {status_text}")

        msg = "\n".join(lines)
        self.send_message(chat_id, msg)
        return msg

    def _handle_materials_request(self, chat_id: int) -> str:
        """عرض قائمة السنوات الدراسية للمكتبة."""
        msg = "📚 **مكتبة المحاضرات والمواد الرسمية**\nاختر السنة الدراسية لاستعراض ملفاتها:"
        keyboard = {
            'inline_keyboard': [
                [{'text': 'سنة اولى 1️⃣', 'callback_data': 'year_1'}, {'text': 'سنة ثانية 2️⃣', 'callback_data': 'year_2'}],
                [{'text': 'سنة ثالثة 3️⃣', 'callback_data': 'year_3'}, {'text': 'سنة رابعة 4️⃣', 'callback_data': 'year_4'}],
                [{'text': 'سنة خامسة 5️⃣', 'callback_data': 'year_5'}],
            ]
        }
        self.send_message(chat_id, msg, reply_markup=keyboard)
        return msg

    def _handle_claim_prompt(self, tg_user: TelegramUser, chat_id: int) -> str:
        """إرشاد الطالب لإتمام ربط الحساب."""
        msg = (
            "🔐 **ربط وتوثيق الهوية الأكاديمية**\n\n"
            "لربط حسابك بسجلك الجامعي، أرسل رقمك الامتحاني بالصيغة:\n"
            "`/claim <رقم_الامتحان>`\n\n"
            "مثال:\n`/claim 12345`"
        )
        self.send_message(chat_id, msg)
        return msg
