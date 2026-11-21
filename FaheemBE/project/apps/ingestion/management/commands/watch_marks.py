from django.core.management.base import BaseCommand
from apps.ingestion.marks_watcher import MarksWatcherService
from apps.operations.services import OutboxDispatcherService


class Command(BaseCommand):
    help = "المراقبة التلقائية لملفات علامات الكلية الجديدة ومعالجتها فورياً"

    def add_arguments(self, parser):
        parser.add_argument('--folder-id', type=str, help='معرف مجلد العلامات في درايف')
        parser.add_argument('--url', type=str, help='رابط ملف PDF مباشر من موقع الكلية')
        parser.add_argument('--course', type=str, default='مقرر جامعي', help='اسم المقرر عند التنزيل من رابط')

    def handle(self, *args, **options):
        self.stdout.write("⏳ جارٍ فحص مصادر علامات الكلية للتحقق من صدور نتائج جديدة...")

        url = options.get('url')
        if url:
            course = options.get('course')
            self.stdout.write(f"🌐 فحص الرابط المباشر: {url}...")
            job = MarksWatcherService.check_and_ingest_from_url(url, course)
            if job:
                self.stdout.write(self.style.SUCCESS(f"✔ تم استخراج ومعالجة ملف العلامات بنجاح! مهمة رقم: {job.id}"))
                self.stdout.write(self.style.SUCCESS(f"📊 عدد الطلاب المستخرجين: {job.match_candidates.count()}"))
            else:
                self.stdout.write("ℹ الملف معالج مسبقاً بنفس البصمة أو تعذر تنزيله.")
        else:
            folder_id = options.get('folder_id')
            jobs = MarksWatcherService.check_and_ingest_from_drive_folder(marks_folder_id=folder_id)
            if jobs:
                self.stdout.write(self.style.SUCCESS(f"✔ تم رصد واستخراج {len(jobs)} ملف علامات جديد بنجاح!"))
                # بث الإشعارات
                OutboxDispatcherService.dispatch_pending_events()
            else:
                self.stdout.write("ℹ لا توجد ملفات علامات جديدة غير معالجة في المجلد.")
