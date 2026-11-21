from typing import Optional, Tuple
from .models import TelegramUser, StudentClaimRequest, ClaimStatus


def get_or_create_telegram_user(
    telegram_id: int,
    username: Optional[str] = None,
    first_name: str = "",
    last_name: str = ""
) -> Tuple[TelegramUser, bool]:
    """استرجاع أو إنشاء مستخدم تليغرام وتحديث بياناته."""
    user, created = TelegramUser.objects.get_or_create(
        telegram_id=telegram_id,
        defaults={
            'username': username,
            'first_name': first_name,
            'last_name': last_name
        }
    )
    if not created and (user.username != username or user.first_name != first_name):
        user.username = username
        user.first_name = first_name
        user.last_name = last_name
        user.save(update_fields=['username', 'first_name', 'last_name', 'last_interaction_at'])
    return user, created


def get_user_claim_request(telegram_user: TelegramUser) -> Optional[StudentClaimRequest]:
    """جلب أحدث طلب ربط حساب للمستخدم."""
    return StudentClaimRequest.objects.filter(telegram_user=telegram_user).order_by('-created_at').first()
