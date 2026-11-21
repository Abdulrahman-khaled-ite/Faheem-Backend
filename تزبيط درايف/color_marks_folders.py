# -*- coding: utf-8 -*-
"""
كود مخصص لتلوين كافة مجلدات (علامات جامعية) في Google Drive:
- يجلب المجلدات مباشرة عبر Google Drive API للتغلب على أي تأخير في المزامنة.
- يلون المجلد الرئيسي (علامات جامعية).
- يلون السنوات الخمس (سنة 1، 2، 3، 4، 5).
- يلون مجلدات الاختصاصات (برمجيات، ذكاء، شبكات).
- يلون جميع مجلدات المواد بالكامل بألوان متناسقة ومنسجمة.
- يطبع تقرير تلوين مباشر خطوة بخطوة لكل مجلد.
"""

from google.colab import auth
from googleapiclient.discovery import build
import time

print("🔐 الخطوة 1: جارٍ توثيق الحساب مع Google Drive API...")
auth.authenticate_user()
drive_service = build('drive', 'v3')
print("✔ تم توثيق الحساب بنجاح!\n")

# لوحة الألوان الرسمية
COLOR_PALETTE = {
    # المجلد الرئيسي
    "علامات جامعية": "#4986e7",  # أزرق ملكي

    # السنوات
    "سنة اولى": "#16a765",       # أخضر زمردي
    "سنة ثانية": "#7bd148",      # ليموني حيوي
    "سنة ثالثة": "#b99aff",      # بنفسجي لافندر
    "سنة رابعة": "#ff7537",      # برتقالي دافئ
    "سنة خامسة": "#a479e2",      # أرجواني ملكي

    # الاختصاصات
    "برمجيات": "#4986e7",        # أزرق برمجي
    "ذكاء": "#a479e2",           # بنفسجي / موف
    "شبكات": "#fa573c",          # برتقالي محمر
}

# ألوان المواد التابعة لكل سنة أو اختصاص
YEAR_SUBJECT_COLORS = {
    "سنة اولى": "#16a765",       # أخضر زمردي
    "سنة ثانية": "#7bd148",      # ليموني
    "سنة ثالثة": "#b99aff",      # بنفسجي لافندر
}

BRANCH_SUBJECT_COLORS = {
    "برمجيات": "#4986e7",        # أزرق
    "ذكاء": "#a479e2",           # بنفسجي
    "شبكات": "#fa573c",          # برتقالي
}

def get_children(parent_id):
    """جلب المجلدات الأبناء لمجلد معين مباشرة من API"""
    query = f"'{parent_id}' in parents and mimeType = 'application/vnd.google-apps.folder' and trashed = false"
    items = []
    page_token = None
    while True:
        resp = drive_service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, folderColorRgb)",
            pageSize=100,
            pageToken=page_token
        ).execute()
        items.extend(resp.get('files', []))
        page_token = resp.get('nextPageToken')
        if not page_token:
            break
    return items

def update_folder_color(folder_id, folder_name, color_hex):
    """تلوين مجلد فردي مع معالجة الأخطاء"""
    try:
        drive_service.files().update(
            fileId=folder_id,
            body={'folderColorRgb': color_hex},
            fields='id, name, folderColorRgb'
        ).execute()
        return True, None
    except Exception as e:
        return False, str(e)

print("🔍 الخطوة 2: البحث عن مجلد (علامات جامعية)...")

# البحث عن المجلد
res = drive_service.files().list(
    q="name contains 'علامات جامعية' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
    fields="files(id, name, parents)"
).execute().get('files', [])

if not res:
    res = drive_service.files().list(
        q="name contains 'علامات' and mimeType = 'application/vnd.google-apps.folder' and trashed = false",
        fields="files(id, name, parents)"
    ).execute().get('files', [])

if not res:
    print("❌ لم يتم العثور على أي مجلد باسم 'علامات جامعية'. يرجى التأكد من تشغيل كود الإنشاء أولاً.")
else:
    # اختيار المجلد الصحيح الذي يحتوي على مجلدات السنوات
    chosen_root = None
    for r in res:
        ch = get_children(r['id'])
        if any("سنة" in c['name'] for c in ch):
            chosen_root = r
            break
    if not chosen_root:
        chosen_root = res[0]

    root_folder = chosen_root
    root_id = root_folder['id']
    root_name = root_folder['name']
    print(f"✔ تم العثور على المجلد الرئيسي: [{root_name}] (ID: {root_id})")

    # تلوين المجلد الرئيسي
    ok, err = update_folder_color(root_id, root_name, COLOR_PALETTE["علامات جامعية"])
    if ok:
        print(f"🎨 تم تلوين المجلد الرئيسي: [{root_name}] -> أزرق ملكي ({COLOR_PALETTE['علامات جامعية']})")

    print("\n📂 الخطوة 3: فحص السنوات والمواد وتلوينها بالكامل...")
    
    # جلب السنوات
    years = get_children(root_id)
    print(f"✔ تم العثور على {len(years)} سنوات داخل مجلد العلامات.")

    total_colored = 1 if ok else 0
    errors_count = 0

    for y in years:
        y_name = y['name']
        y_id = y['id']

        # تحديد لون السنة
        y_color = COLOR_PALETTE.get(y_name, "#4986e7")
        for key in COLOR_PALETTE:
            if key in y_name and "سنة" in key:
                y_color = COLOR_PALETTE[key]
                break

        ok, err = update_folder_color(y_id, y_name, y_color)
        if ok:
            print(f"\n📁 [سنة] {y_name} -> تم التلوين ({y_color})")
            total_colored += 1
        else:
            print(f"\n❌ فشل تلوين {y_name}: {err}")
            errors_count += 1

        # جلب محتويات السنة
        sub_items = get_children(y_id)

        for item in sub_items:
            item_name = item['name']
            item_id = item['id']

            # فحص إذا كان المجلد اختصاص (برمجيات، ذكاء، شبكات)
            is_branch = False
            for b_name in ["برمجيات", "ذكاء", "شبكات"]:
                if b_name in item_name:
                    is_branch = True
                    b_color = COLOR_PALETTE[b_name]
                    ok, err = update_folder_color(item_id, item_name, b_color)
                    if ok:
                        print(f"   🏢 [اختصاص] {item_name} -> تم التلوين ({b_color})")
                        total_colored += 1
                    else:
                        errors_count += 1

                    # جلب مواد هذا الاختصاص
                    branch_subjects = get_children(item_id)
                    for subj in branch_subjects:
                        s_name = subj['name']
                        s_id = subj['id']
                        s_color = BRANCH_SUBJECT_COLORS.get(b_name, b_color)
                        ok_s, err_s = update_folder_color(s_id, s_name, s_color)
                        if ok_s:
                            print(f"      📘 [مادة] {s_name}")
                            total_colored += 1
                        else:
                            errors_count += 1
                    break

            # إذا لم يكن اختصاص فهو مقرر مباشر (سنوات 1 و 2 و 3)
            if not is_branch:
                # لون المادة حسب لون السنة
                s_color = y_color
                for yk in YEAR_SUBJECT_COLORS:
                    if yk in y_name:
                        s_color = YEAR_SUBJECT_COLORS[yk]
                        break
                ok_s, err_s = update_folder_color(item_id, item_name, s_color)
                if ok_s:
                    print(f"   📘 [مادة] {item_name}")
                    total_colored += 1
                else:
                    errors_count += 1

    print("\n" + "="*60)
    print(f"🎉 اكتمل التلوين بنجاح تام!")
    print(f"   • إجمالي المجلدات التي تم تلوينها: {total_colored} مجلد.")
    if errors_count > 0:
        print(f"   • الأخطاء: {errors_count} (تم تجاهلها)")
    print("="*60)
    print("💡 ملاحظة مهمة: افتح صفحة Google Drive واضغط Refresh (تحديث / F5) لتظهر الألوان مباشرة في درايف!")
