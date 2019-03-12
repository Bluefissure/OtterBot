#!/usr/bin/env python3
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
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
sys.path.append(settings.BASE_DIR)
os.environ['DJANGO_SETTINGS_MODULE'] = 'FFXIV.settings'
django.setup()
chats = ChatMessage.objects.filter(timestamp__lt=time.time() - 600)
for chat in chats:
    chat.delete()
