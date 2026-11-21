# معمارية النظام والباك إند — منصة فهيم (Faheem Backend Architecture)

**الإصدار:** v2.0  
**البيئة:** Django 6.1.x, Django REST Framework, Python 3.13  
**النمط الهندسي:** نمط المونوث النمطي (Modular Monolith) مع هيكلية الخدمات النظيفة (Service-Layer / Clean Architecture)

---

## 1. المبادئ الهندسية (Engineering Principles & Invariants)

1. **فصل طبقات الأعمال (Clean Architecture & Service Layer):**
   - **النماذج (`Models`):** مسؤولة حصراً عن بنية البيانات والقيود وقواعد التكامل المرجعي (Referential Integrity).
   - **الاستعلامات (`Selectors`):** دوال نقية مسؤولة عن القراءة والتصفية وجلب البيانات المعقدة من قاعدة البيانات.
   - **العمليات والخدمات (`Services`):** مسؤولة عن منطق الأعمال المعقد، الكتابة، الحسابات الذرية، والتكامل الخارجي (Drive / Telegram).
   - **المتحكمات (`Views`):** طبقة خفيفة جداً (Thin Views) تتحقق من الصلاحيات وتمرر الطلبات للمتحكمات وترجع الردود.

2. **فصل الهويات الأكاديمية (Identity Separation):**
   - هوية السجل الأكاديمي الداخلي `AcademicRecord` (مفتاح رقمي `BIGINT`) دائمة ومستقلة تماماً.
   - الرقم الامتحاني السنوي `YearlyExamIdentity` (مكون من 5 خانات) فريد في سنة معينة لجميع المقررات، لكنه يتغير سنوياً.
   - حساب Telegram `TelegramUser` مستقل تماماً، ولا يُربط تلقائياً بالسجل بمجرد تشابه الاسم، بل عبر تدقيق وادعاء ملكية موثق (`StudentClaimRequest`).

3. **سلطة النشر الذري (Atomic Publication Authority):**
   - نطاق النشر الذري هو ثلاثية: `(المقرر + السنة الأكاديمية + الدورة الامتحانية)`.
   - قفل النطاق على مستوى الصف (Row-Level Lock) يضمن عدم تضارب النشر المتزامن.
   - خدمة الاستخراج `ingestion` لا تملك أي صلاحية كتابة في جدول العلامات الرسمية `current_grades`، بل تقدم أدلة ومرشحي مطابقة تُعتمد رسمياً في `academic`.

4. **نمط الصندوق الصادر الموثوق (Transactional Outbox):**
   - أي حدث نشر أو تعديل علامات يُسجل ذرياً كـ `OutboxEvent` في نفس المعاملة، ويقوم عمال المعالجة بإرسال إشعارات Telegram ومزامنة الحالات بدون فقدان أو تكرار.

---

## 2. هيكلية المجلدات والتطبيقات (`apps/`)

```text
FaheemBE/project/
├── manage.py
├── .env / .env.example
├── project/
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── apps/
    ├── academic/            # النواة الأكاديمية ونماذج الـ ERD
    │   ├── models/          # نماذج السجلات، المقررات، العلامات، الأصول
    │   ├── services/        # خدمات النشر، اشتقاق المعدلات، إثبات الأصل
    │   ├── selectors/       # استعلامات السجلات والعلامات والطلاب
    │   ├── serializers/     # متسلسلات DRF للتحقق من البيانات
    │   ├── views/           # واجهات العرض الأكاديمية
    │   └── urls.py
    │
    ├── drive_sync/          # التكامل مع Google Drive ومكتبة المحاضرات
    │   ├── models/          # DriveFile, SourceRevision, EducationalMaterial
    │   ├── services/        # DriveClient, FolderScanner, SyncService
    │   ├── selectors/       # استعلام المواد والمجلدات والملفات
    │   ├── serializers/     # متسلسلات ملفات المواد الدراسية
    │   ├── views/
    │   └── urls.py
    │
    ├── ingestion/           # خط استخراج علامات PDF والمطابقة الذكية
    │   ├── models/          # ProcessingJob, Attempt, Artifact, MatchCandidate
    │   ├── extractors/      # استخراج النصوص والجداول من PDF والتطبيع العربي
    │   ├── services/        # MatchingEngine, ExtractionPipeline
    │   ├── selectors/
    │   ├── serializers/
    │   └── urls.py
    │
    ├── telegram_bot/        # واجهة بوت تليغرام للطالب والإدارة
    │   ├── models/          # TelegramUser, ClaimRequest, InteractionLog
    │   ├── handlers/        # معالجات الأوامر (/start, /results, /materials)
    │   ├── services/        # BotService, KeyboardBuilder, WebhookManager
    │   ├── views/           # Webhook Callback Endpoint
    │   └── urls.py
    │
    ├── operations/          # الصندوق الصادر والمهام الخلفية وتتبع العمليات
    │   ├── models/          # OutboxEvent, ConsumerReceipt, NotificationAttempt
    │   ├── services/        # EventDispatcher, NotificationService
    │   └── urls.py
    │
    └── api/                 # نقطة التجميع المركزية لراوتات الـ REST API
        ├── urls.py          # /api/v1/...
        └── views.py
```

---

## 3. مخطط تدفق البيانات (Data Flow)

### مسار استخراج ونشر العلامات:
```
Google Drive PDF 
      ↓ (اكتشاف ملف جديد عبر drive_sync)
SourceRevision Created 
      ↓ (إنشاء مهمة في ingestion)
ProcessingJob & PyMuPDF Extraction 
      ↓ (تطبيع الأسماء العربية واستخراج رقم الامتحان والعلامة)
IdentityMatchCandidates Generated 
      ↓ (تحقق النواة في academic)
Atomic Publication Transaction (قفل Scope + كتابة CurrentGrades + تسجيل Provenance)
      ↓ (تسجيل الحدث ذرياً)
OutboxEvent Created 
      ↓ (إرسال الإشعارات)
Telegram Bot Notification to Verified Students
```

### مسار استعلام الطالب عبر تليغرام:
```
Telegram Student (/results)
      ↓
Telegram Webhook Receiver (Idempotent Update Check)
      ↓
Bot Service -> Academic Selectors (جلب العلامات الحالية المعتمدة مع توضيح حالة النشر)
      ↓
Formatted Arabic Markdown Reply with Inline Keyboards
```

---

## 4. تعليمات التشغيل وتوليد الـ Migrations

### 1. إعداد البيئة الافتراضية
البيئة الافتراضية متوفرة في `FaheemBE`:
```powershell
# تفعيل البيئة على ويندوز
.\FaheemBE\Scripts\Activate.ps1
```

### 2. توليد وتطبيق المايجريشنز (Migrations)
```powershell
cd "D:\antigravity Projects\Faheem\FaheemBE\project"
python manage.py makemigrations academic drive_sync ingestion telegram_bot operations
python manage.py migrate
```

### 3. تشغيل خادم التطوير
```powershell
python manage.py runserver
```
