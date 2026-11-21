from django.core.management.base import BaseCommand
from apps.drive_sync.rbcs_crawler import RBCsLectureCrawlerService
from apps.operations.services import OutboxDispatcherService


class Command(BaseCommand):
    help = "فحص منصة RBCs للمحاضرات ورفع الملفات الجديدة تلقائياً لدرايف وإشعار الطلاب عبر تليغرام"

    def add_arguments(self, parser):
        parser.add_argument('--url', type=str, help='رابط المنصة لفحصه')

    def handle(self, *args, **options):
        self.stdout.write("⏳ جارٍ بدء فحص ومراقبة منصة المحاضرات...")
        custom_url = options.get('url')

        synced = RBCsLectureCrawlerService.crawl_and_sync_new_lectures(platform_url=custom_url)

        if synced:
            self.stdout.write(self.style.SUCCESS(f"✔ تم اكتشاف ومزامنة {len(synced)} محاضرة جديدة بنجاح!"))
            # إرسال إشعارات التليغرام المجدولة في الـ Outbox
            dispatched = OutboxDispatcherService.dispatch_pending_events()
            self.stdout.write(self.style.SUCCESS(f"📢 تم إرسال {dispatched} إشعار للطلاب عبر تليغرام."))
        else:
            self.stdout.write("ℹ لا توجد محاضرات جديدة غير مسبوقة حالياً.")
