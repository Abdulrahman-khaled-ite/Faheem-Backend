# -*- coding: utf-8 -*-
"""
كود Google Colab لإنشاء جداول محاضرات فارغة ومنسقة داخل كل مادة دراسية في Google Drive
كلية الهندسة المعلوماتية - جامعة دمشق
"""

# ==========================================
# 1. ربط Google Drive وتثبيت مكتبة Excel
# ==========================================
from google.colab import drive
import os
import shutil

print("⏳ جارٍ ربط Google Drive...")
drive.mount('/content/drive')

try:
    import openpyxl
except ImportError:
    import subprocess
    subprocess.check_call(['pip', 'install', 'openpyxl', '-q'])
    import openpyxl

from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# ==========================================
# 2. تحديد مسار المجلد الرئيسي في Google Drive
# ==========================================
DEFAULT_PATH = "/content/drive/MyDrive/كلية الهندسة المعلوماتية/مواد دراسة و دورات و سلالم تصحيح و زنقة"

def find_drive_root():
    """البحث الذكي عن مجلد المواد داخل Google Drive"""
    if os.path.exists(DEFAULT_PATH):
        return DEFAULT_PATH
    
    my_drive = "/content/drive/MyDrive"
    if not os.path.exists(my_drive):
        raise FileNotFoundError("لم يتم العثور على Google Drive! يرجى التأكد من الضغط على السماح بربط درايف.")
        
    for root, dirs, _ in os.walk(my_drive):
        for d in dirs:
            if "مواد دراسة" in d or "كلية الهندسة المعلوماتية" in d:
                candidate = os.path.join(root, d)
                if any("سنة" in sub for sub in os.listdir(candidate)):
                    return candidate
    return DEFAULT_PATH

DRIVE_ROOT = find_drive_root()
print(f"📁 المجلد الرئيسي المعتمد في درايف:\n  -> {DRIVE_ROOT}\n")

# ==========================================
# 3. إعدادات التنسيق والألوان وعدد الصفوف الفارغة
# ==========================================
NUM_EMPTY_ROWS = 25  # عدد الصفوف الفارغة في كل جدول

NAVY_HEADER = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
TITLE_FILL  = PatternFill(start_color="0F2439", end_color="0F2439", fill_type="solid")
ZEBRA_ROW   = PatternFill(start_color="F7F9FB", end_color="F7F9FB", fill_type="solid")
WHITE_ROW   = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")

THIN_BORDER = Side(border_style="thin", color="D3D3D3")
CELL_BORDER = Border(left=THIN_BORDER, right=THIN_BORDER, top=THIN_BORDER, bottom=THIN_BORDER)

def create_empty_subject_table(year_name, subject_name):
    """ينشئ جدولاً فارغاً منسقاً بالكامل لمادة معينة"""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "المحاضرات"
    ws.views.sheetView[0].rightToLeft = True

    # شريط العنوان
    ws.merge_cells('A1:I1')
    title_cell = ws['A1']
    title_cell.value = f"جامعة دمشق - كلية الهندسة المعلوماتية | {year_name} - مقرر {subject_name}"
    title_cell.fill = TITLE_FILL
    title_cell.font = Font(name="Segoe UI", size=13, bold=True, color="FFFFFF")
    title_cell.alignment = Alignment(horizontal="center", vertical="center")
    ws.row_dimensions[1].height = 36

    # رؤوس الأعمدة
    headers = [
        "م",
        "رقم المحاضرة",
        "عنوان المحاضرة",
        "نوع المحاضرة",
        "تاريخ المحاضرة",
        "اسم الملف (PDF)",
        "رابط الدرايف (Drive Link)",
        "حالة الدراسة",
        "ملاحظات"
    ]
    ws.append(headers)
    ws.row_dimensions[2].height = 26

    for col_idx in range(1, len(headers) + 1):
        c = ws.cell(row=2, column=col_idx)
        c.fill = NAVY_HEADER
        c.font = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
        c.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)
        c.border = CELL_BORDER

    # صفوف فارغة جاهزة للتعبئة
    for idx in range(1, NUM_EMPTY_ROWS + 1):
        row_num = ws.max_row + 1
        row_fill = ZEBRA_ROW if idx % 2 == 0 else WHITE_ROW
        row_data = [
            idx,
            f"محاضرة {idx}",
            "",  # عنوان المحاضرة (فارغ)
            "نظري",  # نوع المحاضرة
            "",  # تاريخ المحاضرة (فارغ)
            "",  # اسم الملف (فارغ)
            "",  # رابط الدرايف (فارغ)
            "لم تبدأ",  # حالة الدراسة
            ""   # ملاحظات (فارغ)
        ]
        ws.append(row_data)
        ws.row_dimensions[row_num].height = 22

        for c_idx in range(1, len(row_data) + 1):
            cell = ws.cell(row=row_num, column=c_idx)
            cell.fill = row_fill
            cell.font = Font(name="Segoe UI", size=10)
            cell.border = CELL_BORDER
            align = Alignment(horizontal="center", vertical="center") if c_idx in [1, 2, 4, 5, 8] else Alignment(horizontal="right", vertical="center")
            cell.alignment = align

    # أبعاد الأعمدة
    col_widths = {1: 6, 2: 14, 3: 35, 4: 14, 5: 16, 6: 35, 7: 28, 8: 15, 9: 25}
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = 'A3'
    return wb

# ==========================================
# 4. المرور على كل مادة وإنشاء الجدول داخلها
# ==========================================
# أسماء المجلدات الفرعية الثابتة داخل كل مادة لتجنب معاملتها كمادة
SUB_COMPONENTS = {"دورات", "زنقة", "سلالم", "سلايدات", "محاضرات", "ملحق"}

created_count = 0
print("🚀 جارٍ فحص المجلدات في Google Drive وإنشاء الجداول الفارغة...\n")

for year_dir in sorted(os.listdir(DRIVE_ROOT)):
    year_path = os.path.join(DRIVE_ROOT, year_dir)
    if not os.path.isdir(year_path) or year_dir.startswith('.'):
        continue

    print(f"📂 [{year_dir}]:")

    for subj_dir in sorted(os.listdir(year_path)):
        subj_path = os.path.join(year_path, subj_dir)
        if not os.path.isdir(subj_path) or subj_dir.startswith('.'):
            continue

        # تخطي إذا كان المجلد فرعياً
        if subj_dir in SUB_COMPONENTS:
            continue

        # إنشاء جدول المادة الفارغ
        wb = create_empty_subject_table(year_dir, subj_dir)

        # حفظ الجدول في مجلد المادة
        main_table_path = os.path.join(subj_path, f"جدول_محاضرات_{subj_dir}.xlsx")
        wb.save(main_table_path)

        # وإذا وجد مجلد 'محاضرات' داخل المادة، وضع نسخة داخله أيضاً
        lec_folder = os.path.join(subj_path, "محاضرات")
        if os.path.exists(lec_folder) and os.path.isdir(lec_folder):
            shutil.copy2(main_table_path, os.path.join(lec_folder, f"جدول_محاضرات_{subj_dir}.xlsx"))

        print(f"   ✔ {subj_dir} -> تم إنشاء: جدول_محاضرات_{subj_dir}.xlsx")
        created_count += 1

print("\n" + "="*50)
print(f"🎉 تم بنجاح إنشاء {created_count} جدول فارغ لكافة المواد في Google Drive!")
print("💡 جميع الجداول منسقة وتفتح مباشرة في Google Sheets لتعبئتها براحتك.")
print("="*50)
