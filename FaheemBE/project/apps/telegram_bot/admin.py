from django.contrib import admin
from .models import TelegramUser, StudentClaimRequest, InteractionLog


@admin.register(TelegramUser)
class TelegramUserAdmin(admin.ModelAdmin):
    list_display = ('telegram_id', 'username', 'first_name', 'linked_record', 'role', 'is_verified', 'last_interaction_at')
    list_filter = ('is_verified', 'role')
    search_fields = ('telegram_id', 'username', 'first_name', 'last_name')


@admin.register(StudentClaimRequest)
class StudentClaimRequestAdmin(admin.ModelAdmin):
    list_display = ('telegram_user', 'academic_record', 'claimed_exam_number', 'claimed_academic_year', 'status', 'created_at')
    list_filter = ('status', 'claimed_academic_year')
    search_fields = ('claimed_exam_number', 'telegram_user__username', 'academic_record__official_name')


@admin.register(InteractionLog)
class InteractionLogAdmin(admin.ModelAdmin):
    list_display = ('telegram_user', 'update_id', 'command', 'created_at')
    search_fields = ('update_id', 'command')
