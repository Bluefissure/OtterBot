#!/usr/bin/python3
import random
import sys
import os
import codecs
import urllib
import base64
sys.path.append('PATH_TO_FFXIVBOT')
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIVBOT.settings'
from FFXIVBOT import settings
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

