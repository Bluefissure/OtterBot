#!/usr/bin/env python3
from ffxivbot.models import *
from django.db import connection, connections
import string
import django
from FFXIV import settings
import random
import sys
import os
import codecs
import urllib
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'FFXIV.settings'
django.setup()


def add_reply_cnt(num):
    groups = QQGroup.objects.all()
    for item in groups:
        item.left_reply_cnt = min(100, item.left_reply_cnt + num)
        item.save()


add_reply_cnt(60)
