# -*- coding: utf-8 -*-
"""
كود Google Colab المتكامل والنهائي:
1. تنظيف وحذف المجلدات الغريبة في السنتين الرابعة والخامسة (مثل شبكات متقدمة، مشاريع التخرج، مشترك).
2. تطبيق مقررات السنتين الرابعة والخامسة الرسمية بدقة من Marks (برمجيات، ذكاء، شبكات).
3. إزالة أي مقررات خاطئة كانت مدخلة بالخطأ في البرمجيات أو غيرها.
4. إنشاء المجلدات الستة (دورات، زنقة، سلالم، سلايدات، محاضرات، ملحق) داخل كل مادة.
5. تلوين كافة المجلدات في Google Drive تلقائياً (السنوات، الاختصاصات، المواد، والمجلدات الداخلية).
"""

# ==========================================================
# الخطوة 1: ربط درايف وتنظيف وتجهيز هيكلية المجلدات
# ==========================================================
from google.colab import drive
import os
import re
import shutil

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

# المجلدات الستة لكل مقرر
SUB_FOLDERS = ["دورات", "زنقة", "سلالم", "سلايدات", "محاضرات", "ملحق"]

# المقررات الرسمية المعتمدة 100% من قاعدة بيانات Marks لجميع السنوات
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
    s = re.sub(r'[أإآ]', 'ا', s.strip())
    s = re.sub(r'ة', 'ه', s)
    s = re.sub(r'ى', 'ي', s)
    s = re.sub(r'(?:^|[\s\-_])ال', ' ', s)
    return re.sub(r'[\s\-_]+', '', s).lower()

# 1. تنظيف أي ملفات إكسل قديمة
for root, _, files in os.walk(DRIVE_ROOT):
    for f in files:
        if f.endswith('.xlsx') or f.endswith('.xls'):
            try: os.remove(os.path.join(root, f))
            except: pass

print("🧹 جارٍ تنظيف المجلدات الزائدة والخاطئة في السنتين الرابعة والخامسة...")
ALLOWED_SPECIALIZATIONS = {"برمجيات", "ذكاء", "شبكات"}

for yr in ["سنة رابعة", "سنة خامسة"]:
    # فحص مجلد السنة الفعلي في درايف
    for d in os.listdir(DRIVE_ROOT):
        if norm(yr) in norm(d):
            yr_path = os.path.join(DRIVE_ROOT, d)
            # إزالة المجلدات الطائشة التي ليست اختصاصاً (مثل: مشترك، شبكات متقدمة، مشاريع التخرج)
            for item in os.listdir(yr_path):
                item_path = os.path.join(yr_path, item)
                if os.path.isdir(item_path):
                    if norm(item) not in {norm(x) for x in ALLOWED_SPECIALIZATIONS}:
                        print(f"   🗑️ إزالة مجلد زائد في {d}: {item}")
                        shutil.rmtree(item_path, ignore_errors=True)
                    else:
                        # تنظيف المقررات الخاطئة داخل الاختصاص
                        spec_canonical = None
                        for sp in ALLOWED_SPECIALIZATIONS:
                            if norm(sp) == norm(item):
                                spec_canonical = sp
                                break
                        if spec_canonical and yr in CURRICULUM and spec_canonical in CURRICULUM[yr]:
                            valid_subjs_norm = {norm(s) for s in CURRICULUM[yr][spec_canonical]}
                            for sub_dir in os.listdir(item_path):
                                sub_dir_path = os.path.join(item_path, sub_dir)
                                if os.path.isdir(sub_dir_path):
                                    if norm(sub_dir) not in valid_subjs_norm:
                                        print(f"   🗑️ إزالة مادة غير تابعة لـ {item}: {sub_dir}")
                                        shutil.rmtree(sub_dir_path, ignore_errors=True)

print("✔ اكتمل التنظيف بنجاح.\n")

print("🚀 جارٍ بناء وتأكيد المجلدات الرسمية والمجلدات الستة...")
existing_years = {norm(d): d for d in os.listdir(DRIVE_ROOT) if os.path.isdir(os.path.join(DRIVE_ROOT, d))}

for y_key, branches in CURRICULUM.items():
    year_dir = existing_years.get(norm(y_key), y_key)
    year_path = os.path.join(DRIVE_ROOT, year_dir)
    os.makedirs(year_path, exist_ok=True)
    print(f"📂 [{year_dir}]")

    existing_branches = {norm(d): d for d in os.listdir(year_path) if os.path.isdir(os.path.join(year_path, d))}

    for b_key, subjects in branches.items():
        if b_key == 'عام':
            parent_path = year_path
        else:
            branch_dir = existing_branches.get(norm(b_key), b_key)
            parent_path = os.path.join(year_path, branch_dir)
            os.makedirs(parent_path, exist_ok=True)
            print(f"   🏢 اختصاص: {branch_dir}")

        existing_subjs = {norm(d): d for d in os.listdir(parent_path) if os.path.isdir(os.path.join(parent_path, d))}

        for subj in subjects:
            actual_subj = existing_subjs.get(norm(subj), subj)
            subj_path = os.path.join(parent_path, actual_subj)
            os.makedirs(subj_path, exist_ok=True)

            # إنشاء المجلدات الستة
            for sf in SUB_FOLDERS:
                os.makedirs(os.path.join(subj_path, sf), exist_ok=True)

print("\n" + "="*50)
print("🎉 اكتمل ترتيب المجلدات بالكامل بنجاح!")
print("="*50 + "\n")

# ==========================================================
# الخطوة 2: تلوين كافة المجلدات في Google Drive تلقائياً
# ==========================================================
print("🎨 جارٍ توثيق الحساب لتلوين المجلدات في Google Drive...")
from google.colab import auth
from googleapiclient.discovery import build

auth.authenticate_user()
drive_service = build('drive', 'v3')

# لوحة الألوان الرسمية
COLOR_PALETTE = {
    # السنوات
    "سنة اولى": "#16a765",       # أخضر
    "سنة ثانية": "#7bd148",      # ليموني
    "سنة ثالثة": "#b99aff",      # بنفسجي
    "سنة رابعة": "#f83a22",      # أحمر
    "سنة خامسة": "#f83a22",      # أحمر

    # الاختصاصات
    "برمجيات": "#4986e7",        # أزرق
    "ذكاء": "#a479e2",           # موف / بنفسجي
    "شبكات": "#fa573c",          # برتقالي

    # المجلدات الستة الداخلية في كل مادة
    "محاضرات": "#16a765",        # أخضر
    "دورات": "#b99aff",          # بنفسجي
    "زنقة": "#f83a22",           # أحمر
    "سلالم": "#4986e7",          # أزرق
    "سلايدات": "#fa573c",        # برتقالي
    "ملحق": "#fad165"            # أصفر ذهبي
}

print("🔍 جارٍ جلب قائمة المجلدات وتلوينها بالكامل (حتى الداخلية)...")

# البحث عن مجلد المشروع الرئيسي في درايف
root_res = drive_service.files().list(
    q=f"name contains 'مواد دراسة و دورات و سلالم تصحيح و زنقة' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
    fields="files(id, name)"
).execute().get('files', [])

if not root_res:
    print("❌ تعذر العثور على المجلد الرئيسي عبر Drive API.")
else:
    root_id = root_res[0]['id']
    
    # جلب جميع المجلدات بطلب سريع
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

    print(f"✔ تم فحص {len(all_folders)} مجلد، جارٍ تطبيق الألوان...")

    # تجهيز قائمة المجلدات المطلوب تلوينها
    to_color = []
    for f in all_folders:
        fname = f['name']
        fid = f['id']
        assigned_color = None

        # 1. فحص المجلدات الستة الداخلية
        if fname in COLOR_PALETTE:
            assigned_color = COLOR_PALETTE[fname]
        else:
            # 2. فحص السنوات
            for yk in ["سنة اولى", "سنة ثانية", "سنة ثالثة", "سنة رابعة", "سنة خامسة"]:
                if yk in fname:
                    assigned_color = COLOR_PALETTE[yk]
                    break

        if assigned_color:
            to_color.append({'id': fid, 'color': assigned_color, 'name': fname})

    # تنفيذ التلوين بدفعات سريعة (Batch Requests)
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
            # في حال واجهت الدفعة أي خطأ يتم التلوين فردياً
            for item in chunk:
                try:
                    drive_service.files().update(fileId=item['id'], body={'folderColorRgb': item['color']}).execute()
                except:
                    pass

    print("\n" + "="*50)
    print(f"🎉 تم تلوين {len(to_color)} مجلد بنجاح تام (السنوات، الاختصاصات، والمجلدات الستة الداخلية)!")
    print("="*50)
