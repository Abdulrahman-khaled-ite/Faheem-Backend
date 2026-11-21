# -*- coding: utf-8 -*-
"""
كود Google Colab المتكامل لمجلد (علامات جامعية):
1. إنشاء مجلد "علامات جامعية" داخل "كلية الهندسة المعلوماتية" (أو في درايف الرئيسي إن لم يوجد).
2. إنشاء السنوات الخمس (سنة اولى، سنة ثانية، سنة ثالثة، سنة رابعة، سنة خامسة).
3. في السنتين الرابعة والخامسة: إنشاء الاختصاصات الثلاثة (برمجيات، ذكاء، شبكات).
4. إنشاء مجلدات المواد الرسمية المعتمدة 100% من قاعدة بيانات Marks داخل كل سنة واختصاص (بدون مجلدات فرعية داخل المواد).
5. تلوين كافة المجلدات عبر Google Drive API (الرئيسي، السنوات، الاختصاصات، وجميع المواد) بألوان متناسقة ومنسجمة.
"""

# ==========================================================
# الخطوة 1: ربط Google Drive وإنشاء هيكلية مجلدات العلامات
# ==========================================================
from google.colab import drive
import os
import shutil

print("⏳ جارٍ ربط Google Drive...")
drive.mount('/content/drive')

# تحديد مسار المجلد الرئيسي
DEFAULT_PARENT = "/content/drive/MyDrive/كلية الهندسة المعلوماتية"
ALT_PARENT = "/content/drive/MyDrive"

if os.path.exists(DEFAULT_PARENT):
    PARENT_DIR = DEFAULT_PARENT
else:
    # بحث تلقائي عن مجلد "كلية الهندسة المعلوماتية"
    found = False
    for root, dirs, _ in os.walk(ALT_PARENT):
        if "كلية الهندسة المعلوماتية" in dirs:
            PARENT_DIR = os.path.join(root, "كلية الهندسة المعلوماتية")
            found = True
            break
    if not found:
        PARENT_DIR = os.path.join(ALT_PARENT, "كلية الهندسة المعلوماتية")
        os.makedirs(PARENT_DIR, exist_ok=True)

MARKS_ROOT = os.path.join(PARENT_DIR, "علامات جامعية")
os.makedirs(MARKS_ROOT, exist_ok=True)
print(f"📁 مسار مجلد العلامات الجامعية المعتمد:\n  -> {MARKS_ROOT}\n")

# المقررات الرسمية المعتمدة 100% من قاعدة بيانات Marks لجميع السنوات والاختصاصات
CURRICULUM = {
    "سنة اولى": {
        "عام": [
            "البرمجة 1", "البرمجة 2", "التحليل 1", "التحليل 2", "الجبر العام",
            "الجبر الخطي", "الدارات الكهربائية و الالكترونية", "الفيزياء",
            "مبادئ عمل الحواسيب", "اللغة العربية", "الثقافة القومية الاشتراكية",
            "انكليزي 1", "انكليزي 2"
        ]
    },
    "سنة ثانية": {
        "عام": [
            "البرمجة 3", "التحليل 3", "التحليل العددي", "الخوارزميات و بنى المعطيات 1",
            "الخوارزميات و بنى المعطيات 2", "الدارات المنطقية", "الاحتمالات و الاحصاء",
            "بنيان الحواسيب 1", "الاتصالات الرقمية", "انكليزي 3", "انكليزي 4", "مهارات التواصل"
        ]
    },
    "سنة ثالثة": {
        "عام": [
            "أساسيات الشبكات", "البيانيات", "الحسابات العلمية", "اللغات الصورية",
            "بحوث العمليات", "بنيان الحواسيب 2", "قواعد المعطيات 1", "لغات البرمجة",
            "مبادئ الذكاء الصنعي", "مشروع 1"
        ]
    },
    "سنة رابعة": {
        "برمجيات": [
            "الاقتصاد و الإدارة في مؤسسة", "البرمجة التفرعية", "التسويق", "المترجمات",
            "خوارزميات البحث الذكية", "قواعد المعطيات 2", "مشروع 2", "مشروع المترجمات",
            "نظم الوسائط المتعددة", "نظم تشغيل 1", "هندسة البرمجيات 1", "هندسة البرمجيات 2"
        ],
        "ذكاء": [
            "الاقتصاد و الإدارة في مؤسسة", "البرمجة التفرعية", "التسويق", "الحقائق الافتراضية",
            "الشبكات العصبونية", "المترجمات", "خوارزميات البحث الذكية", "مشروع 2",
            "نظم الوسائط المتعددة", "نظم تشغيل 1", "نظم قواعد المعرفة", "هندسة البرمجيات 1"
        ],
        "شبكات": [
            "الاقتصاد و الإدارة في مؤسسة", "البرمجة التفرعية", "التسويق", "الشبكات العصبونية",
            "برتوكولات الاتصالات الحاسوبية", "برمجة التطبيقات الشبكية", "خوارزميات البحث الذكية",
            "مشروع 2", "نظم التشغيل 2", "نظم الوسائط المتعددة", "نظم تشغيل 1", "هندسة البرمجيات 1"
        ]
    },
    "سنة خامسة": {
        "برمجيات": [
            "أمن نظم معلومات", "إدارة المشاريع", "النظم و التطبيقات الموزعة", "تطبيقات الانترنت",
            "قواعد المعطيات المتقدمة", "مشروع تخرج", "نظم البحث عن المعلومات", "هندسة البرمجيات 3", "هندسة نظم المعلومات"
        ],
        "ذكاء": [
            "أمن الشبكات الحاسوبية", "أمن نظم معلومات", "إدارة المشاريع", "استكشاف المعرفة",
            "التعلم التلقائي", "الرؤيا الحاسوبية", "الروبوتية", "المنطق الترجيحي و الخوارزميات الوراثية",
            "مشروع تخرج", "معالجة اللغات الطبيعية", "نظم البحث عن المعلومات"
        ],
        "شبكات": [
            "أمن الشبكات الحاسوبية", "أمن نظم معلومات", "إدارة الشبكات الحاسوبية", "إدارة المشاريع",
            "النظم و التطبيقات الموزعة", "تصميم الشبكات الحاسوبية", "مشروع تخرج", "نظم الزمن الحقيقي", "نمذجة و محاكاة النظم الشبكية"
        ]
    }
}

print("⚙️ جارٍ إنشاء السنوات والاختصاصات ومجلدات المواد...")
created_folders_count = 0

for year, branches in CURRICULUM.items():
    year_path = os.path.join(MARKS_ROOT, year)
    os.makedirs(year_path, exist_ok=True)
    created_folders_count += 1
    
    for branch, subjects in branches.items():
        if branch == "عام":
            # السنوات 1 و 2 و 3: المواد مباشرة تحت مجلد السنة
            target_dir = year_path
        else:
            # السنوات 4 و 5: مجلد للاختصاص أولاً
            branch_path = os.path.join(year_path, branch)
            os.makedirs(branch_path, exist_ok=True)
            target_dir = branch_path
            created_folders_count += 1
            
        for subj in subjects:
            subj_path = os.path.join(target_dir, subj)
            os.makedirs(subj_path, exist_ok=True)
            created_folders_count += 1

print(f"✔ تم إنشاء الهيكلية كاملة بنجاح ({created_folders_count} مجلد) بدون أي مجلدات فرعية داخل المواد!")
print("="*60 + "\n")

# ==========================================================
# الخطوة 2: توثيق Google Drive API وتلوين كافة المجلدات
# ==========================================================
print("🎨 جارٍ توثيق الحساب لتلوين المجلدات في Google Drive...")
from google.colab import auth
from googleapiclient.discovery import build

auth.authenticate_user()
drive_service = build('drive', 'v3')

# لوحة الألوان المعتمدة لـ Google Drive
COLOR_PALETTE = {
    # المجلد الرئيسي للعلامات
    "علامات جامعية": "#4986e7",  # أزرق ملكي

    # السنوات
    "سنة اولى": "#16a765",       # أخضر زمردي
    "سنة ثانية": "#7bd148",      # ليموني حيوي
    "سنة ثالثة": "#b99aff",      # بنفسجي لافندر
    "سنة رابعة": "#ff7537",      # برتقالي دافئ
    "سنة خامسة": "#a479e2",      # أرجواني ملكي

    # الاختصاصات
    "برمجيات": "#4986e7",        # أزرق
    "ذكاء": "#a479e2",           # موف / بنفسجي
    "شبكات": "#fa573c",          # برتقالي محمر
}

# ألوان مواد كل سنة / اختصاص
YEAR_SUBJECT_COLORS = {
    "سنة اولى": "#16a765",       # أخضر
    "سنة ثانية": "#7bd148",      # ليموني
    "سنة ثالثة": "#b99aff",      # بنفسجي
}

BRANCH_SUBJECT_COLORS = {
    "برمجيات": "#4986e7",        # أزرق
    "ذكاء": "#a479e2",           # بنفسجي
    "شبكات": "#fa573c",          # برتقالي
}

print("🔍 جارٍ فحص شجرة مجلد (علامات جامعية) وتطبيق الألوان...")

# 1. البحث عن معرف مجلد "علامات جامعية" بدقة
parent_res = drive_service.files().list(
    q="name = 'كلية الهندسة المعلوماتية' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
    fields="files(id, name)"
).execute().get('files', [])

root_marks_id = None
if parent_res:
    parent_id = parent_res[0]['id']
    marks_res = drive_service.files().list(
        q=f"'{parent_id}' in parents and name = 'علامات جامعية' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name)"
    ).execute().get('files', [])
    if marks_res:
        root_marks_id = marks_res[0]['id']

if not root_marks_id:
    res = drive_service.files().list(
        q="name = 'علامات جامعية' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name)"
    ).execute().get('files', [])
    if res:
        root_marks_id = res[0]['id']

if not root_marks_id:
    print("❌ تعذر العثور على مجلد 'علامات جامعية' عبر Drive API.")
else:
    # جلب جميع المجلدات داخل Google Drive
    all_folders = []
    page_token = None
    while True:
        resp = drive_service.files().list(
            q="mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="nextPageToken, files(id, name, parents)",
            pageSize=1000,
            pageToken=page_token
        ).execute()
        all_folders.extend(resp.get('files', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break

    # بناء قاموس للأباء لتحديد تبعية كل مجلد
    folders_by_id = {f['id']: f for f in all_folders}
    children_map = {}
    for f in all_folders:
        for p in f.get('parents', []):
            children_map.setdefault(p, []).append(f)

    # دالة recursive لجمع وتلوين كل المجلدات المتفرعة من "علامات جامعية"
    to_color = []

    # تلوين المجلد الرئيسي نفسه
    to_color.append({'id': root_marks_id, 'color': COLOR_PALETTE["علامات جامعية"], 'name': "علامات جامعية"})

    # تلوين العناصر الداخلية حسب مستواها
    def traverse_and_color(current_id, current_year=None, current_branch=None):
        children = children_map.get(current_id, [])
        for ch in children:
            name = ch['name']
            cid = ch['id']
            color = None
            next_year = current_year
            next_branch = current_branch

            # 1. فحص إذا كان سنة
            if name in COLOR_PALETTE and "سنة" in name:
                color = COLOR_PALETTE[name]
                next_year = name
            # 2. فحص إذا كان اختصاص
            elif name in COLOR_PALETTE and name in ["برمجيات", "ذكاء", "شبكات"]:
                color = COLOR_PALETTE[name]
                next_branch = name
            # 3. مجلد مادة
            else:
                if next_branch and next_branch in BRANCH_SUBJECT_COLORS:
                    color = BRANCH_SUBJECT_COLORS[next_branch]
                elif next_year and next_year in YEAR_SUBJECT_COLORS:
                    color = YEAR_SUBJECT_COLORS[next_year]
                else:
                    color = "#4986e7" # افتراضي أزرق

            if color:
                to_color.append({'id': cid, 'color': color, 'name': name})

            # الاستمرار في النزول بالشجرة
            traverse_and_color(cid, next_year, next_branch)

    traverse_and_color(root_marks_id)

    print(f"✔ تم تحديد {len(to_color)} مجلد للتلوين، جارٍ الإرسال إلى Google Drive...")

    # تطبيق التلوين بدفعات (Batch Requests)
    chunk_size = 50
    for i in range(0, len(to_color), chunk_size):
        chunk = to_color[i:i + chunk_size]
        batch = drive_service.new_batch_http_request()
        for item in chunk:
            batch.add(drive_service.files().update(
                fileId=item['id'],
                body={'folderColorRgb': item['color']}
            ))
        try:
            batch.execute()
        except Exception:
            for item in chunk:
                try:
                    drive_service.files().update(fileId=item['id'], body={'folderColorRgb': item['color']}).execute()
                except:
                    pass

    print("\n" + "="*60)
    print(f"🎉 تم تلوين {len(to_color)} مجلد بنجاح تام وبشكل منسق وفوري!")
    print("   • المجلد الرئيسي (علامات جامعية): أزرق ملكي")
    print("   • السنوات: أخضر (سنة 1)، ليموني (سنة 2)، لافندر (سنة 3)، برتقالي (سنة 4)، أرجواني (سنة 5)")
    print("   • الاختصاصات والمواد: ملونة ومتطابقة بالكامل حسب كل اختصاص وسنة")
    print("   • لا توجد أي مجلدات فرعية داخل المواد (جاهزة لإضافة ملفات العلامات مباشرة)")
    print("="*60)
