# -*- coding: utf-8 -*-
"""
كود تلوين مجلدات Google Drive تلقائياً بألوان مميزة:
- تلوين السنوات (سنة اولى: أخضر، ثانية: ليموني، ثالثة: بنفسجي، رابعة وخامسة: أحمر).
- تلوين الاختصاصات (برمجيات: أزرق، ذكاء: بنفسجي، شبكات: برتقالي).
- تلوين المجلدات الستة (محاضرات: أخضر، دورات: بنفسجي، زنقة: أحمر، سلايدات: برتقالي، سلالم: أزرق، ملحق: أصفر).
"""

from google.colab import auth
from googleapiclient.discovery import build
import time

print("🎨 جارٍ توثيق الحساب للاتصال بـ Google Drive API...")
auth.authenticate_user()
drive_service = build('drive', 'v3')

# خريطة ألوان جوجل درايف الرسمية (Google Drive Palette)
COLOR_PALETTE = {
    # السنوات (مطابقة لصورة درايف الخاصة بك)
    "سنة اولى": "#16a765",      # أخضر
    "سنة ثانية": "#7bd148",     # ليموني
    "سنة ثالثة": "#b99aff",     # بنفسجي
    "سنة رابعة": "#f83a22",     # أحمر
    "سنة خامسة": "#f83a22",     # أحمر

    # الاختصاصات
    "برمجيات": "#4986e7",       # أزرق
    "ذكاء": "#a479e2",          # موف / بنفسجي
    "شبكات": "#fa573c",         # برتقالي

    # المجلدات الستة الفرعية
    "محاضرات": "#16a765",       # أخضر
    "دورات": "#b99aff",         # بنفسجي
    "زنقة": "#f83a22",          # أحمر
    "سلالم": "#4986e7",         # أزرق
    "سلايدات": "#fa573c",       # برتقالي
    "ملحق": "#fad165"           # أصفر ذهبي
}

def get_folder_id(folder_name, parent_id=None):
    """البحث عن ID مجلد بالاسم والأب"""
    q = f"name = '{folder_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    if parent_id:
        q += f" and '{parent_id}' in parents"
    res = drive_service.files().list(q=q, fields="files(id, name)").execute()
    files = res.get('files', [])
    return files[0]['id'] if files else None

def set_color(file_id, hex_color):
    """تطبيق اللون على المجلد في درايف"""
    try:
        drive_service.files().update(fileId=file_id, body={'folderColorRgb': hex_color}).execute()
        return True
    except Exception as e:
        return False

# البحث عن المجلد الرئيسي
root_name = "مواد دراسة و دورات و سلالم تصحيح و زنقة"
res = drive_service.files().list(
    q=f"name contains '{root_name}' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
    fields="files(id, name)"
).execute()

files = res.get('files', [])
if not files:
    print("❌ لم يتم العثور على المجلد الرئيسي عبر API. تأكد من الاسم.")
else:
    root_id = files[0]['id']
    print(f"✔ تم العثور على المجلد الرئيسي بنجاح (ID: {root_id})")
    print("🚀 جارٍ تلوين مجلدات السنوات والاختصاصات والمجلدات الـ 6...\n")

    # 1. تلوين مجلدات السنوات
    years_res = drive_service.files().list(
        q=f"'{root_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name)"
    ).execute()

    for y in years_res.get('files', []):
        y_name = y['name']
        y_id = y['id']
        for color_key, col in COLOR_PALETTE.items():
            if color_key in y_name:
                set_color(y_id, col)
                print(f"  🎨 تلوين السنة: {y_name}")
                break

        # 2. تلوين الاختصاصات والمواد داخل السنة
        sub_res = drive_service.files().list(
            q=f"'{y_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
            fields="files(id, name)"
        ).execute()

        for s in sub_res.get('files', []):
            s_name = s['name']
            s_id = s['id']
            # فحص إذا كان اختصاص
            if s_name in ["برمجيات", "ذكاء", "شبكات"]:
                set_color(s_id, COLOR_PALETTE[s_name])
                print(f"     🎨 تلوين اختصاص: {s_name}")
            
            # 3. تلوين المجلدات الـ 6 الفرعية داخل المادة
            inner_res = drive_service.files().list(
                q=f"'{s_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
                fields="files(id, name)"
            ).execute()
            for inner in inner_res.get('files', []):
                i_name = inner['name']
                i_id = inner['id']
                if i_name in COLOR_PALETTE:
                    set_color(i_id, COLOR_PALETTE[i_name])

    print("\n" + "="*50)
    print("🎉 تم تلوين جميع المجلدات في Google Drive بنجاح!")
    print("="*50)
