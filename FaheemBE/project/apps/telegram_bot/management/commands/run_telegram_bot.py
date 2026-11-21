from django.core.management.base import BaseCommand
from apps.telegram_bot.management.commands.run_bot import Command as RunBotCommand


class Command(RunBotCommand):
    help = "تشغيل بوت تليغرام محلياً بنمط الـ Long-Polling (run_telegram_bot alias)"
