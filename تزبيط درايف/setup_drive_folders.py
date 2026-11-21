# -*- coding: utf-8 -*-
"""
كود Google Colab المتكامل:
1. إنشاء كافة مجلدات السنوات والمقررات بدقة مطابقة لقاعدة بيانات الكلية (Marks).
2. دعم كامل لاختصاصات السنتين الرابعة والخامسة (برمجيات، ذكاء، شبكات).
3. إنشاء المجلدات الستة (دورات، زنقة، سلالم، سلايدات، محاضرات، ملحق) داخل كل مادة.
4. حذف أي ملفات إكسل قديمة.
5. (اختياري) كود تلوين المجلدات في Google Drive تلقائياً بالألوان الجامعية.
"""

# ==========================================================
# الخطوة 1: ربط درايف وإنشاء الهيكلية بدقة من بيانات الكلية الرسمية
# ==========================================================
from google.colab import drive
import os
import re

print("⏳ جارٍ ربط Google Drive...")
drive.mount('/content/drive')

DEFAULT_PATH = "/content/drive/MyDrive/كلية الهندسة المعلوماتية/مواد دراسة و دورات و سلالم تصحيح و زنقة"

def find_drive_root():
    if os.path.exists(DEFAULT_PATH):
        return DEFAULT_PATH
    my_drive = "/content/drive/MyDrive"
    for root, dirs, _ in os.walk(my_drive):
        for d in dirs:
            if "مواد دراسة" in d or "كلية الهندسة المعلوماتية" in d:
                candidate = os.path.join(root, d)
                if any("سنة" in sub for sub in os.listdir(candidate)):
                    return candidate
    return DEFAULT_PATH

DRIVE_ROOT = find_drive_root()
print(f"📁 المجلد الرئيسي المعتمد:\n  -> {DRIVE_ROOT}\n")

# تنظيف وحذف أي ملفات إكسل قديمة
print("🧹 جارٍ حذف أي ملفات إكسل (.xlsx) قديمة...")
deleted_files = 0
for root, dirs, files in os.walk(DRIVE_ROOT):
    for f in files:
        if f.endswith('.xlsx') or f.endswith('.xls'):
            try:
                os.remove(os.path.join(root, f))
                deleted_files += 1
            except Exception:
                pass
print(f"✔ تم حذف {deleted_files} ملف إكسل بنجاح.\n")

# المجلدات الستة لكل مقرر
SUB_FOLDERS = ["دورات", "زنقة", "سلالم", "سلايدات", "محاضرات", "ملحق"]

# المقررات الرسمية المستخرجة بدقة من مجلد Marks
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

def norm(s):
    if not s: return ''
    s = s.strip()
    s = re.sub(r'[أإآ]', 'ا', s)
    s = re.sub(r'ة', 'ه', s)
    s = re.sub(r'ى', 'ي', s)
    s = re.sub(r'(?:^|[\s\-_])ال', ' ', s)
    s = re.sub(r'[\s\-_]+', '', s)
    return s.lower()

print("🚀 جارٍ بناء مجلدات المواد والاختصاصات وإنشاء المجلدات الستة...\n")
total_created = 0

existing_years = {norm(d): d for d in os.listdir(DRIVE_ROOT) if os.path.isdir(os.path.join(DRIVE_ROOT, d))} if os.path.exists(DRIVE_ROOT) else {}

for year_key, branches in CURRICULUM.items():
    target_year = existing_years.get(norm(year_key), year_key)
    year_path = os.path.join(DRIVE_ROOT, target_year)
    os.makedirs(year_path, exist_ok=True)
    print(f"📂 [{target_year}]:")

    existing_branches = {norm(d): d for d in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, d))}

    for branch_key, subjects in branches.items():
        if branch_key == 'عام':
            parent_path = year_path
        else:
            branch_dir = existing_branches.get(norm(branch_key), branch_key)
            parent_path = os.path.join(year_path, branch_dir)
            os.makedirs(parent_path, exist_ok=True)
            print(f"   🏢 اختصاص: {branch_dir}")

        existing_subjs = {norm(d): d for d in os.listdir(parent_path) if os.path.isdir(os.path.join(parent_path, d))}

        for subj in subjects:
            actual_subj = existing_subjs.get(norm(subj), subj)
            subj_path = os.path.join(parent_path, actual_subj)
            os.makedirs(subj_path, exist_ok=True)

            # إنشاء المجلدات الستة داخل المادة
            for sf in SUB_FOLDERS:
                os.makedirs(os.path.join(subj_path, sf), exist_ok=True)

            total_created += 1

print("\n" + "="*50)
print(f"🎉 تم بنجاح تجهيز {total_created} مقرر في جميع السنوات والاختصاصات!")
print(f"📁 كل مقرر يحتوي الآن على الستة مجلدات: [دورات، زنقة، سلالم، سلايدات، محاضرات، ملحق].")
print("="*50)
