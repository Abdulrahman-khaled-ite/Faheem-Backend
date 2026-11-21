import json
from pathlib import Path
from django.core.management.base import BaseCommand
from apps.academic.models import Course, AcademicYear, ExamSession


class Command(BaseCommand):
    help = "بذر مقررات كلية الهندسة المعلوماتية والسنوات والدورات من ملف curriculum_complete.json"

    def handle(self, *args, **options):
        self.stdout.write("⏳ جارٍ تهيئة السنوات الأكاديمية والدورات الامتحانية...")

        # 1. إنشاء السنوات الأكاديمية
        years_data = [
            ("2024-2025", 2024),
            ("2025-2026", 2025),
            ("2026-2027", 2026)
        ]
        created_years = []
        for label, start in years_data:
            yr, _ = AcademicYear.objects.get_or_create(label=label, defaults={'start_year': start})
            created_years.append(yr)

            # إنشاء الدورات الامتحانية لكل سنة
            sessions = [
                ("الفصل الأول / دورة أولى", 1),
                ("الفصل الثاني / دورة ثانية", 2),
                ("الدورة التكميلية", 3)
            ]
            for s_label, order in sessions:
                ExamSession.objects.get_or_create(
                    academic_year=yr,
                    official_order=order,
                    defaults={'label': s_label}
                )

        self.stdout.write(self.style.SUCCESS("✔ تم إنشاء السنوات والدورات الامتحانية بنجاح."))

        # 2. قراءة ملف المنهاج
        json_path = Path("D:/antigravity Projects/Faheem/تزبيط درايف/curriculum_complete.json")
        if not json_path.exists():
            self.stderr.write(f"ملف المنهاج غير موجود في: {json_path}")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            curriculum = json.load(f)

        year_mapping = {
            "سنة اولى": 1,
            "سنة ثانية": 2,
            "سنة ثالثة": 3,
            "سنة رابعة": 4,
            "سنة خامسة": 5
        }

        total_courses = 0
        for year_str, depts in curriculum.items():
            year_num = year_mapping.get(year_str, 1)
            for dept_name, courses_list in depts.items():
                for c_name in courses_list:
                    course, created = Course.objects.get_or_create(
                        name=c_name.strip(),
                        original_study_year=year_num,
                        department=dept_name.strip(),
                        defaults={'semester': 1}
                    )
                    if created:
                        total_courses += 1

        self.stdout.write(self.style.SUCCESS(f"✔ تم استيراد وبذر {total_courses} مقرراً دراسياً بنجاح."))
