# -*- coding: utf-8 -*-
"""
Builder script to generate create_tables_colab.py and انشاء_جداول_درايف.ipynb
"""

import json
import zlib
import base64
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
json_path = os.path.join(BASE_DIR, 'subjects_data.json')

with open(json_path, 'r', encoding='utf-8') as f:
    raw = f.read().encode('utf-8')

b64_data = base64.b64encode(zlib.compress(raw, level=9)).decode('ascii')

colab_template = '''# -*- coding: utf-8 -*-
"""
كود Google Colab لإنشاء جداول المحاضرات والمقررات مباشرة داخل مجلدات Google Drive
كلية الهندسة المعلوماتية - جامعة دمشق
"""

# ==========================================
# 1. ربط Google Drive وتثبيت المكتبات المطلوبة
# ==========================================
from google.colab import drive
import os
import re
import json
import zlib
import base64
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
# المسار الظاهر في درايف حسب هيكلية حسابك:
DEFAULT_DRIVE_PATH = "/content/drive/MyDrive/كلية الهندسة المعلوماتية/مواد دراسة و دورات و سلالم تصحيح و زنقة"

def find_drive_root():
    """البحث الذكي عن مجلد المواد داخل Google Drive"""
    if os.path.exists(DEFAULT_DRIVE_PATH):
        return DEFAULT_DRIVE_PATH
    
    my_drive = "/content/drive/MyDrive"
    if not os.path.exists(my_drive):
        raise FileNotFoundError("لم يتم العثور على Google Drive! يرجى التأكد من الضغط على السماح بربط درايف.")
        
    for root, dirs, _ in os.walk(my_drive):
        for d in dirs:
            if "مواد دراسة" in d or "كلية الهندسة المعلوماتية" in d:
                candidate = os.path.join(root, d)
                if any("سنة" in sub for sub in os.listdir(candidate)):
                    return candidate
    return DEFAULT_DRIVE_PATH

DRIVE_ROOT = find_drive_root()
print(f"📁 المجلد الرئيسي المعتمد في درايف:\\n  -> {DRIVE_ROOT}")
os.makedirs(DRIVE_ROOT, exist_ok=True)

# ==========================================
# 3. استرجاع بيانات المحاضرات والمقررات (823 محاضرة)
# ==========================================
# فحص إذا قام المستخدم برفع ملف subjects_data.json أو استخدام البيانات المضمنة تلقائياً
DATA_EMBEDDED = """__B64_DATA_PLACEHOLDER__"""

if os.path.exists('subjects_data.json'):
    print("✔ تم تحميل البيانات من ملف subjects_data.json المرفوع.")
    with open('subjects_data.json', 'r', encoding='utf-8') as f:
        data_by_year = json.load(f)
else:
    raw_json = zlib.decompress(base64.b64decode(DATA_EMBEDDED.encode('ascii'))).decode('utf-8')
    data_by_year = json.loads(raw_json)

# ==========================================
# 4. دوال التنسيق والتطبيع والربط
# ==========================================
NAVY_HEADER = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
ZEBRA_ROW   = PatternFill(start_color="F7F9FB", end_color="F7F9FB", fill_type="solid")
WHITE_ROW   = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
TITLE_FILL  = PatternFill(start_color="0F2439", end_color="0F2439", fill_type="solid")

FONT_TITLE  = Font(name="Segoe UI", size=13, bold=True, color="FFFFFF")
FONT_HEADER = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
FONT_DATA   = Font(name="Segoe UI", size=10, color="000000")

THIN_BORDER = Side(border_style="thin", color="D3D3D3")
CELL_BORDER = Border(left=THIN_BORDER, right=THIN_BORDER, top=THIN_BORDER, bottom=THIN_BORDER)

def norm(s):
    if not s: return ''
    s = s.strip()
    s = re.sub(r'[أإآ]', 'ا', s)
    s = re.sub(r'ة', 'ه', s)
    s = re.sub(r'ى', 'ي', s)
    s = re.sub(r'(?:^|[\\s\\-_])ال', ' ', s)
    s = re.sub(r'[\\s\\-_]+', '', s)
    return s.lower()

def style_cell(cell, fill=None, font=None, alignment=None, border=None):
    if fill: cell.fill = fill
    if font: cell.font = font
    if alignment: cell.alignment = alignment
    if border: cell.border = border

def build_subject_sheet(ws, year_name, subject_name, lectures):
    ws.views.sheetView[0].rightToLeft = True

    # شريط العنوان
    ws.merge_cells('A1:I1')
    title_cell = ws['A1']
    title_cell.value = f"جامعة دمشق - كلية الهندسة المعلوماتية | {year_name} - مقرر {subject_name} ({len(lectures)} محاضرة)"
    style_cell(title_cell, fill=TITLE_FILL, font=FONT_TITLE, alignment=Alignment(horizontal="center", vertical="center"))
    ws.row_dimensions[1].height = 36

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
        style_cell(c, fill=NAVY_HEADER, font=FONT_HEADER, alignment=Alignment(horizontal="center", vertical="center", wrap_text=True), border=CELL_BORDER)

    row_start = 3
    if lectures:
        for idx, lec in enumerate(lectures, start=1):
            row_num = row_start + idx - 1
            row_fill = ZEBRA_ROW if idx % 2 == 0 else WHITE_ROW
            row_data = [
                idx,
                lec.get('num', '') or f"محاضرة {idx}",
                lec.get('title', ''),
                lec.get('type', 'نظري'),
                lec.get('date', ''),
                lec.get('filename', ''),
                "",  # رابط الدرايف فارغ ليعبئه المستخدم
                "لم تبدأ",
                ""   # الملاحظات فارغة
            ]
            ws.append(row_data)
            ws.row_dimensions[row_num].height = 22
            for c_idx in range(1, len(row_data) + 1):
                cell = ws.cell(row=row_num, column=c_idx)
                align = Alignment(horizontal="center", vertical="center") if c_idx in [1, 2, 4, 5, 8] else Alignment(horizontal="right", vertical="center")
                style_cell(cell, fill=row_fill, font=FONT_DATA, alignment=align, border=CELL_BORDER)
    else:
        # قوالب فارغة جاهزة للتعبئة
        for idx in range(1, 16):
            row_num = row_start + idx - 1
            row_fill = ZEBRA_ROW if idx % 2 == 0 else WHITE_ROW
            row_data = [idx, f"محاضرة {idx}", "", "نظري", "", "", "", "لم تبدأ", ""]
            ws.append(row_data)
            ws.row_dimensions[row_num].height = 22
            for c_idx in range(1, len(row_data) + 1):
                cell = ws.cell(row=row_num, column=c_idx)
                align = Alignment(horizontal="center", vertical="center") if c_idx in [1, 2, 4, 5, 8] else Alignment(horizontal="right", vertical="center")
                style_cell(cell, fill=row_fill, font=FONT_DATA, alignment=align, border=CELL_BORDER)

    col_widths = {1: 5, 2: 14, 3: 35, 4: 12, 5: 16, 6: 35, 7: 28, 8: 15, 9: 25}
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = 'A3'

# ==========================================
# 5. التوليد التلقائي لجميع الجداول في Drive
# ==========================================
print("\\n🚀 جارٍ إنشاء الجداول داخل مجلدات Google Drive...")

master_wb = openpyxl.Workbook()
master_wb.remove(master_wb.active)

summary_ws = master_wb.create_sheet(title="الملخص العام")
summary_ws.views.sheetView[0].rightToLeft = True
summary_ws.merge_cells('A1:E1')
s_title = summary_ws['A1']
s_title.value = "جامعة دمشق - كلية الهندسة المعلوماتية | الدليل الشامل لكافة المقررات والمحاضرات"
style_cell(s_title, fill=TITLE_FILL, font=FONT_TITLE, alignment=Alignment(horizontal="center", vertical="center"))
summary_ws.row_dimensions[1].height = 36

sum_headers = ["م", "السنة الدراسية", "اسم المادة", "عدد المحاضرات", "مجلد المادة في الدرايف"]
summary_ws.append(sum_headers)
summary_ws.row_dimensions[2].height = 26
for c_idx in range(1, len(sum_headers) + 1):
    c = summary_ws.cell(row=2, column=c_idx)
    style_cell(c, fill=NAVY_HEADER, font=FONT_HEADER, alignment=Alignment(horizontal="center", vertical="center"), border=CELL_BORDER)

global_counter = 1
total_lectures = 0

existing_years = {norm(d): d for d in os.listdir(DRIVE_ROOT) if os.path.isdir(os.path.join(DRIVE_ROOT, d))} if os.path.exists(DRIVE_ROOT) else {}

for year_name, subjects in data_by_year.items():
    norm_y = norm(year_name)
    target_year_dir_name = existing_years.get(norm_y, year_name)
    year_folder = os.path.join(DRIVE_ROOT, target_year_dir_name)
    os.makedirs(year_folder, exist_ok=True)

    existing_subjs = {norm(d): d for d in os.listdir(year_folder) if os.path.isdir(os.path.join(year_folder, d))}

    year_wb = openpyxl.Workbook()
    year_wb.remove(year_wb.active)

    for subj_name, lectures in subjects.items():
        total_lectures += len(lectures)
        
        r_num = summary_ws.max_row + 1
        r_fill = ZEBRA_ROW if global_counter % 2 == 0 else WHITE_ROW
        summary_ws.append([global_counter, year_name, subj_name, len(lectures), f"{target_year_dir_name}/{subj_name}"])
        summary_ws.row_dimensions[r_num].height = 22
        for c_idx in range(1, 6):
            cell = summary_ws.cell(row=r_num, column=c_idx)
            align = Alignment(horizontal="center", vertical="center") if c_idx in [1, 2, 4] else Alignment(horizontal="right", vertical="center")
            style_cell(cell, fill=r_fill, font=FONT_DATA, alignment=align, border=CELL_BORDER)
        global_counter += 1

        clean_sheet_title = subj_name.replace('/', '-').strip()
        y_ws = year_wb.create_sheet(title=clean_sheet_title[:31])
        build_subject_sheet(y_ws, year_name, subj_name, lectures)

        subj_clean = subj_name.replace('/', '-').strip()
        single_wb = openpyxl.Workbook()
        single_wb.remove(single_wb.active)
        s_ws = single_wb.create_sheet(title="المحاضرات")
        build_subject_sheet(s_ws, year_name, subj_name, lectures)

        norm_s = norm(subj_name)
        target_subj_dir_name = existing_subjs.get(norm_s, subj_clean)
        subj_dir = os.path.join(year_folder, target_subj_dir_name)
        os.makedirs(subj_dir, exist_ok=True)

        single_path = os.path.join(subj_dir, f"جدول_محاضرات_{subj_clean}.xlsx")
        single_wb.save(single_path)

        lec_subfolder = os.path.join(subj_dir, "محاضرات")
        if os.path.exists(lec_subfolder) and os.path.isdir(lec_subfolder):
            shutil.copy2(single_path, os.path.join(lec_subfolder, f"جدول_محاضرات_{subj_clean}.xlsx"))

    year_wb_path = os.path.join(year_folder, f"جدول_مواد_{target_year_dir_name}.xlsx")
    year_wb.save(year_wb_path)
    print(f"  ✔ تم إنشاء جداول {year_name} ({len(subjects)} مادة)")

s_col_widths = {1: 6, 2: 18, 3: 30, 4: 22, 5: 35}
for col_idx, width in s_col_widths.items():
    summary_ws.column_dimensions[get_column_letter(col_idx)].width = width
summary_ws.freeze_panes = 'A3'

master_path = os.path.join(DRIVE_ROOT, "الجدول_الشامل_لكافة_المقررات_والمحاضرات.xlsx")
master_wb.save(master_path)

print("\\n" + "="*50)
print("🎉 تم إنجاز العمل بنجاح على Google Drive!")
print(f"📊 إجمالي المقررات: {global_counter - 1}")
print(f"📚 إجمالي المحاضرات المدرجة: {total_lectures}")
print(f"📁 المجلد الرئيسي في درايف:\\n  -> {DRIVE_ROOT}")
print("="*50)
print("💡 ملاحظة: ملفات Excel (.xlsx) تفتح مباشرة في Google Sheets وتتيح لك التعديل وتعبئة الروابط والملاحظات بنقرة واحدة!")
'''

full_colab_code = colab_template.replace('__B64_DATA_PLACEHOLDER__', b64_data)

colab_py_path = os.path.join(BASE_DIR, 'create_tables_colab.py')
with open(colab_py_path, 'w', encoding='utf-8') as f:
    f.write(full_colab_code)

print("Generated create_tables_colab.py successfully!")

# Also generate a Jupyter Notebook (.ipynb)
notebook = {
    "cells": [
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# 📚 توليد جداول المحاضرات والمقررات في Google Drive\n",
                "### كلية الهندسة المعلوماتية - جامعة دمشق\n",
                "يقوم هذا الكود بإنشاء:\n",
                "1. **جدول Excel مستقل لكل مقرر** داخل مجلد المادة ومجلد المحاضرات في Drive.\n",
                "2. **جدول شامل لكل سنة دراسية** داخل مجلد السنة.\n",
                "3. **جدول شامل للكلية بالكامل** داخل المجلد الرئيسي.\n",
                "\n",
                "> جميع الجداول منسقة باللغة العربية (RTL) مع ألوان أنيقة ورؤوس مثبتة، وتفتح مباشرة كـ Google Sheets."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [line + "\n" for line in full_colab_code.split("\n")]
        }
    ],
    "metadata": {
        "colab": {
            "name": "انشاء_جداول_درايف.ipynb",
            "provenance": []
        },
        "language_info": {
            "name": "python"
        }
    },
    "nbformat": 4,
    "nbformat_minor": 0
}

ipynb_path = os.path.join(BASE_DIR, 'انشاء_جداول_درايف.ipynb')
with open(ipynb_path, 'w', encoding='utf-8') as f:
    json.dump(notebook, f, ensure_ascii=False, indent=2)

import sys
sys.stdout.reconfigure(encoding='utf-8')
print("Generated انشاء_جداول_درايف.ipynb successfully!")
