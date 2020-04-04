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
from django.urls import path
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.conf import settings
from django.views.decorators.cache import cache_page

from ffxivbot.views import *
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', tata),
    path('tata/', tata),
    path('quest/', quest),
    path('quest/tooltip/', quest_tooltip),
    path('api/', api),
    path('http/', qqpost),
    path('wechat/message', wechatpost),
    path('image/', image),
    # path('hunt/', cache_page(60 * 2)()),
    path('hunt/', hunt),
    url(r'^oauth/qq/login/$', qq_login, name='qq_login'),
    url(r'^api/qqcallback', qq_check, name='qq_check'),
    # url(r'^oauth/qq/check/$', qq_check, name='qq_check'),
    # url(r'^oauth/bind/account/$', bind_account, name='bind_account'),
    url(r'^login/', login),
    url(r'^register/', register),
    url(r'^logout/', logout),
]
if settings.DEBUG:
    urlpatterns += staticfiles_urlpatterns()
