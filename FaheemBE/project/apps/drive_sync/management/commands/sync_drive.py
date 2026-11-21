import time
from django.core.management.base import BaseCommand
from apps.drive_sync.services import GoogleDriveService
from apps.drive_sync.models import DriveFile, EducationalMaterial, MaterialCategory, StudyDepartment


class Command(BaseCommand):
    help = "فحص ومزامنة شجرة Google Drive الكاملة وتخزين المراجع في DriveFile و EducationalMaterial"

    def handle(self, *args, **options):
        self.stdout.write("⏳ جارٍ تهيئة عميل Google Drive...")
        service = GoogleDriveService()

        if not service.is_configured():
            self.stdout.write(self.style.ERROR("❌ عميل Drive غير مهيأ. تأكد من وجود credentials.json."))
            return

        root_folder_id = service.config.get('GOOGLE_DRIVE_ROOT_FOLDER_ID')
        self.stdout.write(f"📁 فحص المجلد الرئيسي: {root_folder_id}")

        root_files = service.list_folder_contents(root_folder_id)
        materials_root_id = None
        marks_root_id = None

        for item in root_files:
            service.register_or_update_file(item, parent_folder_id=root_folder_id, drive_path=f"/{item['name']}")
            if 'مواد دراسة' in item['name']:
                materials_root_id = item['id']
            elif 'علامات' in item['name']:
                marks_root_id = item['id']

        if not materials_root_id:
            self.stdout.write(self.style.WARNING("لم يتم العثور على مجلد المواد الرئيسي."))
            return

        self.stdout.write(self.style.SUCCESS(f"✔ تم العثور على مجلد المواد الرئيسي: {materials_root_id}"))

        # جلب السنوات
        years_folders = service.list_folder_contents(materials_root_id)
        year_mapping = {
            "سنة اولى": 1,
            "سنة ثانية": 2,
            "سنة ثالثة": 3,
            "سنة رابعة": 4,
            "سنة خامسة": 5
        }

        total_indexed_materials = 0

        for y_item in years_folders:
            y_name = y_item['name'].strip()
            study_year_num = year_mapping.get(y_name, 1)
            service.register_or_update_file(y_item, parent_folder_id=materials_root_id, drive_path=f"/مواد/{y_name}")
            self.stdout.write(f"📂 فحص {y_name} ({y_item['id']})...")

            # جلب محتويات السنة (إما مواد مباشرة أو اختصاصات)
            sub_items = service.list_folder_contents(y_item['id'])

            for sub in sub_items:
                sub_name = sub['name'].strip()

                # فحص إن كان المجلد اختصاصاً (برمجيات، ذكاء، شبكات، عام)
                if sub_name in ['برمجيات', 'ذكاء', 'شبكات', 'عام']:
                    dept_name = sub_name
                    service.register_or_update_file(sub, parent_folder_id=y_item['id'], drive_path=f"/مواد/{y_name}/{dept_name}")
                    course_items = service.list_folder_contents(sub['id'])
                else:
                    dept_name = 'عام'
                    course_items = [sub]

                for course_item in course_items:
                    c_name = course_item['name'].strip()
                    c_path = f"/مواد/{y_name}/{dept_name}/{c_name}"
                    service.register_or_update_file(course_item, parent_folder_id=y_item['id'], drive_path=c_path)

                    # جلب المجلدات الستة (دورات، زنقة، سلالم، سلايدات، محاضرات، ملحق)
                    cat_items = service.list_folder_contents(course_item['id'])
                    for cat_item in cat_items:
                        cat_name = cat_item['name'].strip()
                        cat_path = f"{c_path}/{cat_name}"
                        drive_file = service.register_or_update_file(cat_item, parent_folder_id=course_item['id'], drive_path=cat_path)

                        # فهرسة المادة في EducationalMaterial
                        valid_cat = cat_name if cat_name in [c[0] for c in MaterialCategory.choices] else 'أخرى'
                        valid_dept = dept_name if dept_name in [d[0] for d in StudyDepartment.choices] else 'عام'

                        service.index_educational_material(
                            drive_file=drive_file,
                            study_year=study_year_num,
                            department=valid_dept,
                            course_name=c_name,
                            category=valid_cat,
                            title=f"مجلد {cat_name} - {c_name}"
                        )
                        total_indexed_materials += 1

            self.stdout.write(f"  ✔ اكتملت فهرسة {y_name}")

        self.stdout.write(self.style.SUCCESS(f"\n🎉 تمت المزامنة بنجاح! إجمالي المجلدات والمواد المفهرسة: {total_indexed_materials}"))
