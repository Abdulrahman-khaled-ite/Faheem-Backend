# المعمارية الشاملة وتطبيقات النظام — منصة "فهيم" (System Architecture & Apps Reference)

**الإصدار:** v2.0 · Production-Grade Architecture  
**المنصة:** فهيم (Faheem) — منظومة إدارة المحتوى التعليمي والعلامات الرسمية بكلية الهندسة المعلوماتية، جامعة دمشق  
**النمط الهندسي:** Modular Monolith (Clean Architecture & Service Layer)  

---

## 1. نظرة عامة على تطبيقات النظام (`apps/`)

يتألف النظام من 5 تطبيقات رئيسية مستقلة ومنظمة بعناية وفق مبادئ **Clean Architecture** ونمط **Service-Layer**:

```text
FaheemBE/project/apps/
├── academic/       # النواة الأكاديمية وسجلات الطلاب والعلامات ونطاقات النشر الذري
├── drive_sync/     # التكامل الكامل مع Google Drive ومكتبة المحاضرات وزاحف RBCs
├── ingestion/      # خط معالجة واستخراج الـ PDF والمطابقة وتطبيع النصوص العربية
├── telegram_bot/   # واجهة التفاعل الكاملة للطالب والإدارة ومعالج الرفع الذكي (Wizard)
├── operations/     # نمط الصندوق الصادر الموثوق (Transactional Outbox) والأحداث
└── api/            # المجمع المركزي لواجهات الـ REST API (/api/v1/...)
```

### تفصيل أدوار التطبيقات:
1. **`apps.academic` (النواة الأكاديمية):**
   - **النماذج:** `AcademicRecord`, `YearlyExamIdentity`, `Course`, `AcademicYear`, `ExamSession`, `PublicationScope`, `CurrentGrade`, `GradeComponent`, `GradeProvenance`, `PublicationVersion`, `DerivedAcademicState`.
   - **المسؤولية:** الحفاظ على الثوابت الأكاديمية وقفل نطاق النشر الذري وتتبع أصل كل علامة (Provenance) ومنع استبدال العلامات دون سند قطعي.
2. **`apps.drive_sync` (التكامل مع Google Drive والمحتوى التعليمي):**
   - **النماذج:** `DriveFile`, `SourceRevision`, `SourceMetadataObservation`, `EducationalMaterial`.
   - **المسؤولية:** الاتصال المباشر بـ Google Drive API عبر Service Account، إنشاء المجلدات وفق شجرة الكلية الرسمية، رفع وتنزيل الملفات، وزحف محاضرات منصة RBCs.
3. **`apps.ingestion` (خط معالجة العلامات):**
   - **النماذج:** `ProcessingJob`, `ProcessingAttempt`, `ProcessingArtifact`, `IdentityMatchCandidate`.
   - **المسؤولية:** تحليل ملفات الـ PDF بواسطة PyMuPDF، تطبيع الأسماء العربية واستخراج الأرقام الامتحانية والدرجات، وتقديم مقترحات مطابقة موثقة بدون سلطة كتابة مباشرة في العلامات الرسمية.
4. **`apps.telegram_bot` (واجهة تليغرام ومعالج الرفع التفاعلي):**
   - **النماذج:** `TelegramUser`, `StudentClaimRequest`, `InteractionLog`.
   - **المسؤولية:** توفير واجهة محادثة ذكية للطلاب للاستعلام عن المواد والعلامات، ومعالج رفع تفاعلي خطوة بخطوة للمشرفين (Upload Wizard) مربوط مباشرة بالدرايف.
5. **`apps.operations` (الصندوق الصادر وإدارة العمليات):**
   - **النماذج:** `OutboxEvent`, `ConsumerReceipt`, `NotificationAttempt`.
   - **المسؤولية:** ضمان التسليم الموثوق للإشعارات والأحداث بشكل ذري مع حفظ العلامات (Transactional Outbox) وتفادي التكرار.

---

## 2. مخطط حالات الاستخدام (Use Case Diagrams)

### أ. رحلة الطالب (Student User Flow)
```mermaid
flowchart TD
    Student(("🎓 طالب الكلية"))
    
    subgraph Telegram_Student_Interface["واجهة الطالب عبر تليغرام"]
        UC1["بدء المحادثة /start"]
        UC2["تصفح مكتبة المحاضرات والملفات"]
        UC3["اختيار السنة -> التصنيف -> الحصول على رابط درايف"]
        UC4["طلب توثيق وربط الحساب الأكاديمي /claim"]
        UC5["استعراض النتائج والعلامات الرسمية /results"]
    end
    
    Student --> UC1
    UC1 --> UC2
    UC2 --> UC3
    UC1 --> UC4
    UC1 --> UC5
```

### ب. رحلة المشرف ورفع المحتوى (Admin Upload & Management Flow)
```mermaid
flowchart TD
    Admin(("👑 المشرف / ممثل الدفعة"))
    
    subgraph Admin_Wizard_Flow["معالج الرفع الذكي (Interactive Wizard)"]
        A1["طلب الدخول لمنطقة الرفع /admin أو /upload"]
        A2["التحقق والمصادقة بكود المشرفين"]
        A3["اختيار مسار الرفع (علامات / مواد ومحاضرات / سلالم / إعلانات)"]
        A4["تحديد السنة -> الفصل -> التخصص -> المقرر -> المجلد الفرعي"]
        A5["تحديد نمط الرفع (ملف واحد أم حزمة ملفات)"]
        A6["إرسال المستندات عبر تليغرام"]
        A7["حساب البصمة ورفعها تلقائياً للمجلد المناسب في Google Drive"]
    end
    
    Admin --> A1
    A1 --> A2
    A2 -->|نجاح التحقق| A3
    A3 --> A4
    A4 --> A5
    A5 --> A6
    A6 --> A7
```

---

## 3. مخطط الكيانات والعلاقات الكامل (Entity Relationship Diagram - ERD)

```mermaid
erDiagram
    AcademicRecord ||--o{ YearlyExamIdentity : "يملك هويات سنوية"
    AcademicRecord ||--o{ CurrentGrade : "يحصل على علامات"
    AcademicRecord ||--o| TelegramUser : "يرتبط بحساب"
    AcademicRecord ||--o{ DerivedAcademicState : "له معدلات مشتقة"
    AcademicRecord ||--o{ StudentClaimRequest : "له طلبات ربط"

    AcademicYear ||--o{ YearlyExamIdentity : "يحدد السنة"
    AcademicYear ||--o{ ExamSession : "يحتوي دورات"
    AcademicYear ||--o{ PublicationScope : "يشمل نطاقات نشر"

    ExamSession ||--o{ PublicationScope : "يرتبط بنطاق النشر"
    Course ||--o{ PublicationScope : "ينشر له نتائج"

    PublicationScope ||--o{ CurrentGrade : "يحتوي علامات ذرية"
    PublicationScope ||--o{ PublicationVersion : "يسجل إصدارات"

    DriveFile ||--o{ SourceRevision : "له إصدارات بايتات"
    DriveFile ||--o| EducationalMaterial : "يفهرس كمادة"

    SourceRevision ||--o{ GradeProvenance : "مرجع أصل العلامة"
    SourceRevision ||--o{ ProcessingJob : "يخضع لمهمة معالجة"

    GradeProvenance ||--o{ CurrentGrade : "يوثق مصدر العلامة"
    CurrentGrade ||--o{ GradeComponent : "يتكون من أجزاء"

    ProcessingJob ||--o{ ProcessingAttempt : "له محاولات"
    ProcessingJob ||--o{ ProcessingArtifact : "ينتج مخرجات وسيطة"
    ProcessingJob ||--o{ IdentityMatchCandidate : "يولد مرشحي مطابقة"

    TelegramUser ||--o{ InteractionLog : "يسجل تفاعلات"
    TelegramUser ||--o{ StudentClaimRequest : "يقدم طلبات"

    OutboxEvent ||--o{ ConsumerReceipt : "يؤكد استهلاك الحدث"
    OutboxEvent ||--o{ NotificationAttempt : "يسجل محاولات الإشعار"
```

---

## 4. تدفق عملية الرفع التفاعلية عبر التليغرام نحو درايف (Sequence Diagram)

يوضح هذا المخطط تسلسل العمليات الكامل عند قيام مشرف برفع محاضرة أو ملف علامات عبر البوت التفاعلي:

```mermaid
sequenceDiagram
    autonumber
    actor Admin as المشرف (Telegram User)
    participant Bot as Telegram Bot Service
    participant DB as قاعدة البيانات (SQLite / PostgreSQL)
    participant Drive as Google Drive API
    participant Pipeline as Ingestion Pipeline

    Admin->>Bot: يضغط على [📤 رفع وإدارة المحتوى]
    alt المستخدم غير موثق كمشرف
        Bot-->>Admin: يطلب كود المصادقة الخاص بالمشرفين
        Admin->>Bot: يرسل كود المشرفين
        Bot->>DB: يتحقق من الكود ويرقي المستخدم إلى ADMIN
    end

    Bot-->>Admin: الخطوة 1: ماذا تريد أن ترفع؟ (علامات / مواد / دورات / إعلانات)
    Admin->>Bot: يختار [📚 مادة ومحاضرات]
    
    Bot-->>Admin: الخطوة 2: اختر السنة الدراسية (سنة ثانية)
    Admin->>Bot: يختار سنة ثانية
    
    Bot-->>Admin: الخطوة 3: اختر الفصل (الفصل الأول)
    Admin->>Bot: يختار الفصل الأول
    
    Bot-->>Admin: الخطوة 4: اختر المقرر الدراسي (البرمجة 3)
    Admin->>Bot: يختار البرمجة 3
    
    Bot-->>Admin: الخطوة 5: اختر المجلد الفرعي (محاضرات)
    Admin->>Bot: يختار محاضرات
    
    Note over Bot,Drive: حل أو إنشاء المسار تلقائياً في Google Drive
    Bot->>Drive: get_or_create_course_material_folder()
    Drive-->>Bot: إرجاع folder_id الخاص بالمجلد الهدف
    
    Bot-->>Admin: الخطوة 6: هل ترفع ملفاً واحداً أم حزمة متعددة؟
    Admin->>Bot: يختار [📦 حزمة ملفات متعددة]
    
    Bot-->>Admin: جاهز لاستقبال الملفات! أرسل ملفك الآن...
    Admin->>Bot: يرسل ملف PDF المحاضرة
    
    Bot->>Bot: تنزيل الملف وحساب بصمة SHA-256
    Bot->>Drive: upload_file(temp_pdf, folder_id)
    Drive-->>Bot: تأكيد الرفع وإرجاع webViewLink
    
    Bot->>DB: تسجيل في DriveFile وفهرسة في EducationalMaterial
    opt في حال رفع ملف علامات رسمية
        Bot->>Pipeline: إطلاق IngestionPipeline لاستخراج الجداول والدرجات
    end
    
    Bot-->>Admin: ✅ تم الرفع بنجاح! اسم الملف + البصمة + رابط درايف المباشر
```

---

## 5. الخلاصة وضمانات الجودة

- **حماية البيانات والأصل:** لا يتم اعتماد أي علامة أو رفع أي ملف دون حساب بصمة الـ SHA-256 الدقيقة لضمان عدم تلف الملفات أو تكرارها.
- **التدرج في الصلاحيات:** قنوات الاستعلام متاحة لجميع الطلاب، في حين أن مسارات الرفع والقرارات الأكاديمية محصورة بالمشرفين الموثقين.
- **المرونة:** تم بناء النظام ليعمل بكفاءة فائقة على أجهزة التطوير المحلية (باستخدام SQLite و Long-Polling)، كما أنه جاهز بنسبة 100% للنشر السحابي في بيئات الإنتاج (PostgreSQL و Webhooks).
