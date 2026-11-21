# -*- coding: utf-8 -*-
"""
إنشاء جداول المواد والمحاضرات محلياً وفي مجلد مخصص للمزامنة مع جوجل درايف
"""

import os
import sys
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

sys.stdout.reconfigure(encoding='utf-8')

# مسارات المشروع
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, 'subjects_data.json')
OUTPUT_DIR = os.path.join(r"D:\antigravity Projects\مشروع الجامعة الذكي", "جداول_المواد_درايف")

# ألوان وتنسيقات
NAVY_HEADER = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
TEAL_HEADER = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
ZEBRA_ROW   = PatternFill(start_color="F7F9FB", end_color="F7F9FB", fill_type="solid")
WHITE_ROW   = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
TITLE_FILL  = PatternFill(start_color="0F2439", end_color="0F2439", fill_type="solid")

FONT_TITLE  = Font(name="Segoe UI", size=13, bold=True, color="FFFFFF")
FONT_HEADER = Font(name="Segoe UI", size=10, bold=True, color="FFFFFF")
FONT_DATA   = Font(name="Segoe UI", size=10, color="000000")
FONT_BOLD   = Font(name="Segoe UI", size=10, bold=True, color="000000")

THIN_BORDER_SIDE = Side(border_style="thin", color="D3D3D3")
CELL_BORDER = Border(left=THIN_BORDER_SIDE, right=THIN_BORDER_SIDE, top=THIN_BORDER_SIDE, bottom=THIN_BORDER_SIDE)

def style_cell(cell, fill=None, font=None, alignment=None, border=None):
    if fill: cell.fill = fill
    if font: cell.font = font
    if alignment: cell.alignment = alignment
    if border: cell.border = border

def build_subject_sheet(ws, year_name, subject_name, lectures):
    """تنسيق ورقة عمل لمادة معينة"""
    ws.views.sheetView[0].rightToLeft = True

    # شريط العنوان
    ws.merge_cells('A1:I1')
    title_cell = ws['A1']
    title_cell.value = f"جامعة دمشق - كلية الهندسة المعلوماتية | {year_name} - مقرر {subject_name} ({len(lectures)} محاضرة)"
    style_cell(title_cell, fill=TITLE_FILL, font=FONT_TITLE, alignment=Alignment(horizontal="center", vertical="center"))
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
        style_cell(c, fill=NAVY_HEADER, font=FONT_HEADER, alignment=Alignment(horizontal="center", vertical="center", wrap_text=True), border=CELL_BORDER)

    # صفوف البيانات
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
                "",
                "لم تبدأ",
                ""
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

def main():
    with open(DATA_FILE, 'r', encoding='utf-8') as f:
        data_by_year = json.load(f)

    print(f"بدء إنشاء الجداول في المجلد: {OUTPUT_DIR}")
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    # 1. المصنف الشامل لكافة السنوات
    master_wb = openpyxl.Workbook()
    master_wb.remove(master_wb.active)

    summary_ws = master_wb.create_sheet(title="الملخص العام")
    summary_ws.views.sheetView[0].rightToLeft = True
    summary_ws.merge_cells('A1:E1')
    s_title = summary_ws['A1']
    s_title.value = "جامعة دمشق - كلية الهندسة المعلوماتية | الدليل الشامل للمقررات والمحاضرات"
    style_cell(s_title, fill=TITLE_FILL, font=FONT_TITLE, alignment=Alignment(horizontal="center", vertical="center"))
    summary_ws.row_dimensions[1].height = 36

    sum_headers = ["م", "السنة الدراسية", "اسم المادة", "عدد المحاضرات المتوفرة", "مجلد المادة في الدرايف"]
    summary_ws.append(sum_headers)
    summary_ws.row_dimensions[2].height = 26
    for c_idx in range(1, len(sum_headers) + 1):
        cell = summary_ws.cell(row=2, column=c_idx)
        style_cell(cell, fill=NAVY_HEADER, font=FONT_HEADER, alignment=Alignment(horizontal="center", vertical="center"), border=CELL_BORDER)

    global_counter = 1
    total_lectures_all = 0

    for year_name, subjects in data_by_year.items():
        year_folder = os.path.join(OUTPUT_DIR, year_name)
        os.makedirs(year_folder, exist_ok=True)

        # مصنف خاص بالسنة الدراسية
        year_wb = openpyxl.Workbook()
        year_wb.remove(year_wb.active)

        for subj_name, lectures in subjects.items():
            total_lectures_all += len(lectures)
            # إضافة سطر في الملخص
            r_num = summary_ws.max_row + 1
            r_fill = ZEBRA_ROW if global_counter % 2 == 0 else WHITE_ROW
            summary_ws.append([global_counter, year_name, subj_name, len(lectures), f"{year_name}/{subj_name}"])
            summary_ws.row_dimensions[r_num].height = 22
            for c_idx in range(1, 6):
                cell = summary_ws.cell(row=r_num, column=c_idx)
                align = Alignment(horizontal="center", vertical="center") if c_idx in [1, 2, 4] else Alignment(horizontal="right", vertical="center")
                style_cell(cell, fill=r_fill, font=FONT_DATA, alignment=align, border=CELL_BORDER)
            global_counter += 1

            # ورقة في مصنف السنة
            clean_sheet_title = subj_name.replace('/', '-').strip()
            y_ws = year_wb.create_sheet(title=clean_sheet_title[:31])
            build_subject_sheet(y_ws, year_name, subj_name, lectures)

            # ملف Excel مستقل لكل مادة
            subj_clean = subj_name.replace('/', '-').strip()
            single_wb = openpyxl.Workbook()
            single_wb.remove(single_wb.active)
            s_ws = single_wb.create_sheet(title="المحاضرات")
            build_subject_sheet(s_ws, year_name, subj_name, lectures)

            # مجلد المادة
            subj_dir = os.path.join(year_folder, subj_clean)
            os.makedirs(subj_dir, exist_ok=True)
            single_path = os.path.join(subj_dir, f"جدول_محاضرات_{subj_clean}.xlsx")
            single_wb.save(single_path)

        # حفظ مصنف السنة
        year_wb_path = os.path.join(year_folder, f"جدول_مواد_{year_name}.xlsx")
        year_wb.save(year_wb_path)
        print(f"✔ تم إنشاء جداول: {year_name} ({len(subjects)} مادة)")

    # ضبط أعمدة الملخص العام
    s_col_widths = {1: 6, 2: 18, 3: 30, 4: 24, 5: 35}
    for col_idx, width in s_col_widths.items():
        summary_ws.column_dimensions[get_column_letter(col_idx)].width = width
    summary_ws.freeze_panes = 'A3'

    # حفظ المصنف الشامل
    master_path = os.path.join(OUTPUT_DIR, "الجدول_الشامل_لكافة_المقررات_والمحاضرات.xlsx")
    master_wb.save(master_path)
    print(f"\n🎉 تم الانتهاء بنجاح!")
    print(f"📊 إجمالي المقررات: {global_counter - 1}")
    print(f"📚 إجمالي المحاضرات: {total_lectures_all}")
    print(f"📁 مسار المجلد الناتج: {OUTPUT_DIR}")

if __name__ == '__main__':
    main()
