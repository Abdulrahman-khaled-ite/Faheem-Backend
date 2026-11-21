# -*- coding: utf-8 -*-
"""
مولد جداول المقررات والمحاضرات لكلية الهندسة المعلوماتية - جامعة دمشق
يدعم توليد جداول Excel منسقة باحترافية جاهزة للاستخدام على Google Drive و Google Sheets
"""

import os
import re
import json
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# إعدادات التنسيق والألوان
NAVY_HEADER = PatternFill(start_color="1F4E79", end_color="1F4E79", fill_type="solid")
TEAL_HEADER = PatternFill(start_color="2E75B6", end_color="2E75B6", fill_type="solid")
ZEBRA_ROW   = PatternFill(start_color="F2F5F9", end_color="F2F5F9", fill_type="solid")
WHITE_ROW   = PatternFill(start_color="FFFFFF", end_color="FFFFFF", fill_type="solid")
TITLE_FILL  = PatternFill(start_color="0D233A", end_color="0D233A", fill_type="solid")

FONT_TITLE  = Font(name="Segoe UI", size=14, bold=True, color="FFFFFF")
FONT_HEADER = Font(name="Segoe UI", size=11, bold=True, color="FFFFFF")
FONT_DATA   = Font(name="Segoe UI", size=10, color="000000")
FONT_BOLD   = Font(name="Segoe UI", size=10, bold=True, color="000000")

THIN_BORDER_SIDE = Side(border_style="thin", color="D9D9D9")
CELL_BORDER = Border(left=THIN_BORDER_SIDE, right=THIN_BORDER_SIDE, top=THIN_BORDER_SIDE, bottom=THIN_BORDER_SIDE)

def style_cell(cell, fill=None, font=None, alignment=None, border=None):
    if fill: cell.fill = fill
    if font: cell.font = font
    if alignment: cell.alignment = alignment
    if border: cell.border = border

def create_subject_sheet(wb, title, year_name, subject_name, lectures):
    """ينشئ ورقة عمل منسقة لمادة محددة"""
    ws = wb.create_sheet(title=title[:31])
    ws.views.sheetView[0].rightToLeft = True

    # 1. عنوان رئيسي
    ws.merge_cells('A1:I1')
    title_cell = ws['A1']
    title_cell.value = f"كلية الهندسة المعلوماتية | {year_name} - {subject_name} ({len(lectures)} محاضرة)"
    style_cell(title_cell, fill=TITLE_FILL, font=FONT_TITLE, alignment=Alignment(horizontal="center", vertical="center"))
    ws.row_dimensions[1].height = 40

    # 2. رؤوس الأعمدة
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
    ws.row_dimensions[2].height = 28

    for col_idx in range(1, len(headers) + 1):
        c = ws.cell(row=2, column=col_idx)
        style_cell(c, fill=NAVY_HEADER, font=FONT_HEADER, alignment=Alignment(horizontal="center", vertical="center", wrap_text=True), border=CELL_BORDER)

    # 3. تعبئة البيانات
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
                "لم تبدأ",  # الحالة الافتراضية
                ""   # الملاحظات فارغة
            ]
            ws.append(row_data)
            ws.row_dimensions[row_num].height = 22

            for c_idx in range(1, len(row_data) + 1):
                cell = ws.cell(row=row_num, column=c_idx)
                # محاذاة في المنتصف للأعمدة الرقمية والقصيرة
                align = Alignment(horizontal="center", vertical="center") if c_idx in [1, 2, 4, 5, 8] else Alignment(horizontal="right", vertical="center")
                style_cell(cell, fill=row_fill, font=FONT_DATA, alignment=align, border=CELL_BORDER)
    else:
        # إذا لم يكن هناك محاضرات بعد (قالب فارغ جاهز للتعبئة بـ 15 صف)
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

    # 4. ضبط عرض الأعمدة تلقائياً
    col_widths = {
        1: 6,   # م
        2: 14,  # رقم المحاضرة
        3: 35,  # عنوان المحاضرة
        4: 14,  # نوع المحاضرة
        5: 16,  # تاريخ المحاضرة
        6: 35,  # اسم الملف
        7: 28,  # رابط الدرايف
        8: 15,  # حالة الدراسة
        9: 25   # ملاحظات
    }
    for col_idx, width in col_widths.items():
        ws.column_dimensions[get_column_letter(col_idx)].width = width

    ws.freeze_panes = 'A3'
    return ws

def create_single_subject_workbook(year_name, subject_name, lectures, out_filepath):
    """ينشئ ملف Excel مستقل للمادة الواحدة"""
    wb = openpyxl.Workbook()
    wb.remove(wb.active)  # حذف الورقة الافتراضية
    create_subject_sheet(wb, subject_name, year_name, subject_name, lectures)
    os.makedirs(os.path.dirname(out_filepath), exist_ok=True)
    wb.save(out_filepath)
