import time
import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from apps.telegram_bot.services import TelegramBotService


class Command(BaseCommand):
    help = "تشغيل بوت تليغرام محلياً بنمط الـ Long-Polling (بدون الحاجة لـ Webhook أو نطاق عام)"

    def handle(self, *args, **options):
        bot_service = TelegramBotService()
        if not bot_service.url:
            self.stderr.write(self.style.ERROR(
                "❌ خطأ: لم يتم ضبط TELEGRAM_BOT_TOKEN في ملف .env!\n"
                "يرجى جلب التوكن من @BotFather ووضعه في ملف .env ثم إعادة المحاولة."
            ))
            return

        self.stdout.write(self.style.SUCCESS("🚀 بدء تشغيل بوت تليغرام بنمط Long-Polling..."))
        self.stdout.write("اضغط Ctrl+C لإيقاف البوت في أي وقت.")

        # حذف أي webhook سابق لضمان عمل الـ polling بدون تعارض
        try:
            requests.post(f"{bot_service.url}/deleteWebhook", timeout=5)
            self.stdout.write("✔ تم إلغاء أي Webhook سابق لتفعيل الـ Polling المباشر.")
        except Exception as e:
            self.stderr.write(f"تحذير أثناء حذف الـ Webhook: {e}")

        offset = 0
        while True:
            try:
                # طلب التحديثات باستخدام Long-Polling (انتظار حتى 20 ثانية)
                params = {'offset': offset, 'timeout': 20}
                resp = requests.get(f"{bot_service.url}/getUpdates", params=params, timeout=25)

                if resp.status_code == 200:
                    data = resp.json()
                    for update in data.get('result', []):
                        update_id = update['update_id']
                        offset = update_id + 1

                        # معالجة التحديث عبر نفس منطق البوت المعتمد
                        bot_service.handle_webhook_update(update)
                        self.stdout.write(f"📥 تم استقبال ومعالجة تحديث رقم: {update_id}")

                time.sleep(0.5)

            except KeyboardInterrupt:
                self.stdout.write(self.style.WARNING("\n🛑 تم إيقاف البوت."))
                break
            except Exception as ex:
                self.stderr.write(f"خطأ في الاتصال بتليغرام: {ex}")
                time.sleep(3)
