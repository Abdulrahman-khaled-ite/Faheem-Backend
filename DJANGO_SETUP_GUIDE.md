# الدليل العملي الشامل لتنصيب وتشغيل باك إند "فهيم" (Django Setup Guide)

**مشروع:** فهيم (Faheem) — كلية الهندسة المعلوماتية، جامعة دمشق  
**الإصدار:** v2.0  
**المتطلبات الأساسية:** Python 3.11 إلى 3.13 | Git | Windows أو Linux أو macOS  

---

## 1. المتطلبات الأولية (Prerequisites)

قبل البدء، تأكد من تثبيت البرامج التالية على جهازك:
1. **Python (الإصدار 3.11 أو أحدث حتى 3.13):**
   - تحميل من الموقع الرسمي: [python.org](https://www.python.org/downloads/)
   - ⚠️ **هام جداً في ويندوز:** عند التثبيت، فعّل خيار `Add python.exe to PATH`.
2. **Git:** لتنزيل المستودع وإدارته.

---

## 2. خطوات التجهيز والتنصيب خطوة بخطوة

### الخطوة 1: استنساخ المستودع والدخول للمجلد
```powershell
git clone <رابط_المستودع>
cd Faheem
```

---

### الخطوة 2: إنشاء البيئة الافتراضية (Virtual Environment)
في مسار المشروع، أنشئ بيئة بايثون افتراضية مستقلة:
```powershell
# في أنظمة Windows:
python -m venv venv

# في أنظمة Linux / macOS:
python3 -m venv venv
```

---

### الخطوة 3: تفعيل البيئة الافتراضية
```powershell
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1

# Windows (Command Prompt - CMD):
.\venv\Scripts\activate.bat

# Linux / macOS:
source venv/bin/activate
```
*(ستلاحظ ظهور `(venv)` في بداية سطر الأوامر).*

> 💡 **ملاحظة لنظام ويندوز PowerShell:** إذا ظهر لك خطأ `Execution_Policies`، نفّذ الأمر التالي بصلاحيات المسؤول لمرة واحدة:
> `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

---

### الخطوة 4: تثبيت الحزم والمكتبات المطلوبة
قم بتثبيت كافة الاعتماديات من ملف `requirements.txt`:
```powershell
pip install --upgrade pip
pip install -r requirements.txt
```

---

### الخطوة 5: إعداد ملف متغيرات البيئة (`.env`)
انتقل إلى مجلد الـ Django الداخلي:
```powershell
cd FaheemBE/project
```
انسخ ملف `.env.example` وأنشئ ملف `.env`:
```powershell
# في ويندوز:
Copy-Item .env.example .env

# في لينكس / ماك:
cp .env.example .env
```

افتح ملف `.env` بواسطة أي محرر نصوص (مثل VS Code أو Notepad) وتأكد من ملء المتغيرات الأساسية:
```ini
# المفتاح السري وبيئة العمل
SECRET_KEY=django-insecure-your-custom-secret-key-faheem-2026
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# قاعدة البيانات (تلقائياً SQLite محلياً)
DATABASE_URL=sqlite:///db.sqlite3

# توكن بوت تليغرام من @BotFather
TELEGRAM_BOT_TOKEN=ضع_التوكن_الخاص_بك_هنا
TELEGRAM_WEBHOOK_SECRET=faheem_secret_webhook_key_2026
TELEGRAM_ADMIN_PASSCODE=FaheemAdmin2026

# حساب ومعرف درايف الكلية
GOOGLE_ACCOUNT_EMAIL=as.kk.ite.ai@gmail.com
GOOGLE_DRIVE_ROOT_FOLDER_ID=1S2Gyrk8cWTQoOALM1YBYL6fTUEigAmTe
GOOGLE_SERVICE_ACCOUNT_FILE=credentials.json
```

---

### الخطوة 6: وضع ملف مفاتيح غوغل درايف (`credentials.json`)
1. ضع ملف `credentials.json` الذي قمت بتحميله من Google Cloud Console داخل:
   `FaheemBE/project/credentials.json`
2. تأكد من مشاركة مجلد Google Drive الرئيسي (`1S2Gyrk8cWTQoOALM1YBYL6fTUEigAmTe`) مع إيميل الـ Service Account بصلاحية **"محرر" (Editor)**.

---

### الخطوة 7: تطبيق ترحيل الجداول (Migrations)
تأكد أنك داخل المجلد `FaheemBE/project`، ثم نفّذ:
```powershell
python manage.py migrate
```
سيتم إنشاء الـ 35 جدولاً في قاعدة البيانات بنجاح.

---

### الخطوة 8: استيراد وبذر المنهاج الدراسي للكلية (Seed Curriculum)
قم بتشغيل أمر البذر التلقائي لاستيراد الـ 100 مقرر دراسي للسنوات الخمس واختصاصاتها:
```powershell
python manage.py seed_curriculum
```
المخرجات المتوقعة:
```text
✔ تم إنشاء السنوات والدورات الامتحانية بنجاح.
✔ تم استيراد وبذر 100 مقرراً دراسياً بنجاح.
```

---

### الخطوة 9: المزامنة الأولية لمجلدات ومواد Google Drive
قم بتشغيل أمر المزامنة الشاملة لفهرسة شجرة درايف:
```powershell
python manage.py sync_drive
```
سيقوم بجلب وتخزين كافة مجلدات السنوات والمقررات وتصنيفاتها الستة في قاعدة البيانات.

---

## 3. أوامر التشغيل اليومية (Daily Run Commands)

### 1. تشغيل سيرفر الـ API المحلي:
```powershell
python manage.py runserver
```
- لوحة الإدارة (Django Admin): [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/)
- واجهات الـ REST API: [http://127.0.0.1:8000/api/v1/](http://127.0.0.1:8000/api/v1/)

### 2. تشغيل بوت تليغرام "فهيم" (Long-Polling):
في نافذة طرفية منفصلة:
```powershell
python manage.py run_telegram_bot
```
*(أو بالأمر المختصر: `python manage.py run_bot`)*  
يمكنك الآن فتح تليغرام ومراسلة البوت فوراً بالضغط على `/start`!

### 3. تشغيل أتمتة زحف المحاضرات من منصة RBCs:
```powershell
python manage.py crawl_lectures
```

### 4. تشغيل أتمتة مراقبة واستخراج علامات الكلية:
```powershell
python manage.py watch_marks
```

---

## 4. حل المشاكل الشائعة (Troubleshooting)

| المشكلة | السبب المحتمل | الحل |
|---|---|---|
| `ModuleNotFoundError` | لم يتم تفعيل الـ venv أو تثبيت الحزم | شغّل `.\venv\Scripts\Activate.ps1` ثم `pip install -r requirements.txt` |
| `No such file credentials.json` | الملف غير موجود في مكانه المعتمد | ضعه مباشرة في `FaheemBE/project/credentials.json` |
| `Telegram Bot Token is not set` | حقل التوكن فارغ في `.env` | أضف توكن البوت الذي حصلت عليه من `@BotFather` في `.env` |
| `ExecutionPolicy` خطأ في ويندوز | قيود تنفيذ السكربتات في ويندوز | نفذ: `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` |
