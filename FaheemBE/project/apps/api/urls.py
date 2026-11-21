from django.urls import path, include

urlpatterns = [
    path('academic/', include('apps.academic.urls')),
    path('drive/', include('apps.drive_sync.urls')),
    path('ingestion/', include('apps.ingestion.urls')),
    path('telegram/', include('apps.telegram_bot.urls')),
    path('operations/', include('apps.operations.urls')),
]
