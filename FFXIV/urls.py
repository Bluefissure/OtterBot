"""FFXIV URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.0/topics/http/urls/
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
from django.urls import path, re_path, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.decorators.cache import cache_page

from ffxivbot.views import *
from ffxivbot.views.rest import FanshionReportViewSet
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'fashion_report', FanshionReportViewSet, basename='fashion_report')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', tata),
    path('tata/', tata),
    path('quest/', quest),
    path('api/', api),
    path('http/', qqpost),
    # path('wechat/message', wechatpost),
    path('image/', image),
    # path('hunt/', cache_page(60 * 2)()),
    path('hunt/', hunt),
    path('hunt/sonar/', hunt_sonar),
    path('hunt/bird/', hunt_bird),
    path('hunt/relay/', hunt_relay),
    path('housing/api', housing_api),
    re_path(r'^oauth/qq/login/$', qq_login, name='qq_login'),
    re_path(r'^api/qqcallback', qq_check, name='qq_check'),
    re_path(r'^oauth/xivid/login/$', xivid_auth, name='xivid_auth'),
    re_path(r'^oauth/xivid/$', xivid_callback, name='xivid_callback'),
    re_path(r'^dalamud/feedback', dalamud_feedback, name='dalamud_feedback'),
    # url(r'^oauth/qq/check/$', qq_check, name='qq_check'),
    # url(r'^oauth/bind/account/$', bind_account, name='bind_account'),
    re_path(r'^login/', login),
    re_path(r'^register/', register),
    re_path(r'^logout/', logout),
    re_path(r'^auth/szj', szj_auth, name='szj_auth'),
    path('rest/', include(router.urls)),
]
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
