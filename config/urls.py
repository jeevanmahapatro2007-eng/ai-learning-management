from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('apps.core.urls')),
    path('accounts/', include('apps.users.urls')),
    path('courses/', include('apps.courses.urls')),
    path('quizzes/', include('apps.quizzes.urls')),
    path('dashboard/', include('apps.dashboard.urls')),
    path('recommendations/', include('apps.recommendations.urls')),
    path('gamification/', include('apps.gamification.urls')),
    path('notifications/', include('apps.notifications.urls')),
    path('manage-platform/', include('apps.administration.urls')),
    path('api/', include('apps.core.api_urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATICFILES_DIRS[0])
