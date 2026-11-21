# فهيم — منصة الكلية الذكية وبوت الخدمات الأكاديمية (Faheem Platform)

> **Faheem (فهيم):** المنظومة البرمجية المتكاملة لإدارة المحتوى التعليمي، أرشفة المحاضرات، ونشر العلامات والنتائج الرسمية لطلاب كلية الهندسة المعلوماتية — جامعة دمشق عبر تليغرام و Google Drive و REST API.

---

## 📌 نبذة عن المشروع (About The Project)

تم بناء باك إند "فهيم" وفق معايير هندسية متقدمة (**Clean Architecture & Modular Monolith**) باستخدام **Django 6.1** و **Django REST Framework**. يربط النظام بين ثلاث ركائز أساسية:
1. **Google Drive API:** مساحة التخزين السحابية الرسمية للمحاضرات، السلايدات، بنك الدورات، وسلالم التصحيح.
2. **Telegram Bot (@Faheem_ite_bot):** واجهة الطالب للنتائج وتصفح المواد، وبوابة الإدارة التفاعلية (Wizard) لرفع المحتوى وفهرسته.
3. **Ingestion & Outbox Engine:** محرك استخراج علامات الـ PDF آلياً عبر PyMuPDF، ومطابقة الهويات الامتحانية، وبث الإشعارات الموثوقة دون تكرار (Transactional Outbox).

---

## 🚀 البدء السريع للمطور الشريك (Quick Start for Developers)

### 1. استنساخ المستودع (Clone)
```bash
git clone <YOUR_PRIVATE_REPO_URL>
cd Faheem
```

### 2. إعداد البيئة الافتراضية (Virtual Environment)
```bash
# إنشاء البيئة الافتراضية
python -m venv venv

# تفعيل البيئة:
# في ويندوز (PowerShell):
.\venv\Scripts\Activate.ps1
# في ويندوز (CMD):
.\venv\Scripts\activate.bat
# في لينكس / ماك:
source venv/bin/activate

# تثبيت الحزم المطلوبة
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. إعداد ملف البيئة السري (`.env`)
انتقل إلى مجلد المشروع الداخلي:
```bash
cd FaheemBE/project
```
قم بنسخ قالب البيئة:
```bash
# Windows
Copy-Item .env.example .env

# Linux / Mac
cp .env.example .env
```
افتح ملف `.env` واملأ المتغيرات التالية:
- `SECRET_KEY`: مفتاح سري عشوائي لتطوير دجانغو.
- `TELEGRAM_BOT_TOKEN`: التوكن الخاص ببوتك من `@BotFather`.
- `TELEGRAM_ADMIN_PASSCODE`: كود مصادقة المشرفين لرفع الملفات (الافتراضي: `FaheemAdmin2026`).
- `GOOGLE_DRIVE_ROOT_FOLDER_ID`: معرف مجلد درايف الرئيسي (`1S2Gyrk8cWTQoOALM1YBYL6fTUEigAmTe`).

### 4. إعداد مفاتيح Google Drive (`credentials.json`)
- ضع ملف حساب الخدمة `credentials.json` داخل:
  `FaheemBE/project/credentials.json`
- تأكد من مشاركة مجلد Google Drive الرئيسي مع إيميل الـ Service Account بصلاحية **"محرر" (Editor)**.

### 5. تهيئة قاعدة البيانات وبذر المنهاج (Database Setup)
من داخل المجلد `FaheemBE/project`:
```bash
# تطبيق المايجريشنز (35 جدولاً)
python manage.py migrate

# بذر واستيراد المنهاج الدراسي للسنوات الخمس (100 مقرر)
python manage.py seed_curriculum

# مزامنة وفهرسة شجرة Google Drive الكاملة (616 مادة وقسم)
python manage.py sync_drive
```

---

## 💻 أوامر التشغيل اليومية (Run Commands)

```bash
# 1. تشغيل سيرفر الـ API المحلي:
python manage.py runserver

# 2. تشغيل بوت تليغرام محلياً (Long-Polling):
python manage.py run_telegram_bot

# 3. فحص وزحف منصة RBCs للمحاضرات ورفعها لدرايف:
python manage.py crawl_lectures

# 4. مراقبة واستخراج ملفات علامات الكلية آلياً:
python manage.py watch_marks
```

---

## 📂 هيكلية تطبيقات النظام (`apps/`)

- **`apps.academic`:** النواة الأكاديمية، السجلات، المقررات، العلامات، ونطاقات النشر الذري.
- **`apps.drive_sync`:** خدمة الربط مع Google Drive ومكتبة المحاضرات وزاحف RBCs.
- **`apps.ingestion`:** خط معالجة واستخراج علامات الـ PDF وتطبيع الأسماء العربية.
- **`apps.telegram_bot`:** واجهة البوت ومعالج الرفع التفاعلي الذكي (Conversation Wizard).
- **`apps.operations`:** نمط الصندوق الصادر الموثوق (Transactional Outbox) وتتبع الأحداث.
- **`apps.api`:** واجهات الـ REST API المركزية (`/api/v1/`).

---

## 🧪 اختبار الـ APIs عبر Postman
تجد ملف المجموعة الموثق كاملاً في جذر المستودع:  
📄 [`Faheem_API_Collection.json`](Faheem_API_Collection.json)  
قم بعمل `Import` في برنامج Postman، واضبط المتغير `{{base_url}}` (الافتراضي: `http://127.0.0.1:8000/api/v1`).

---

## 📚 وثائق مرجعية إضافية
- 📘 [`DJANGO_SETUP_GUIDE.md`](DJANGO_SETUP_GUIDE.md): دليل مفصل خطوة بخطوة لتنصيب بيئة التطوير.
- 🏗️ [`SYSTEM_ARCHITECTURE_AND_APPS.md`](SYSTEM_ARCHITECTURE_AND_APPS.md): المرجع المعماري الشامل مع مخططات Mermaid (ERD, Use Cases, Sequence Diagrams).
"# Faheem-Backend" 
