"""
URL configuration for TradingDashbackend project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from TradingDashbackend.core import views as core_views
from TradingDashbackend.core.logger import get_application_log
from TradingDashbackend.core.auth import portal_validate_login

urlpatterns = [
    path("", core_views.index),
    path("admin/", admin.site.urls),
    path("login/", portal_validate_login),
    path("api/exec/", admin.site.urls),
    path("api/log/", get_application_log),
    path("__reload__/", include("django_browser_reload.urls")),
]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
