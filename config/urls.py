from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from django.views.generic import TemplateView

urlpatterns = [
    path('', TemplateView.as_view(template_name='index.html'), name='frontend'),
    path('admin/', admin.site.urls),
    path('api/auth/', include('accounts.urls')),
    path('api/missions/', include('missions.urls')),
    path('api/garden/', include('garden.urls')),
    path('api/shop/', include('shop.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
