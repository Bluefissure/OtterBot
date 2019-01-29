#!/usr/bin/env python3
import random
import sys
import os
import codecs
import urllib
import base64

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIV.settings'
from FFXIV import settings
import django
import string
from django.db import connection, connections
django.setup()
from ffxivbot.models import *


def add_reply_cnt(num):
	groups = QQGroup.objects.all()
	for item in groups:
		item.left_reply_cnt = min(100, item.left_reply_cnt+num)
		item.save()


add_reply_cnt(60)
