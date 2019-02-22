#!/usr/bin/env python3
import random
import sys
import os
import codecs
import urllib
import base64
sys.path.append('/root/FFXIVBOT/')
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIV.settings'
from FFXIV import settings
import django
import string
from django.db import connection, connections
django.setup()
from ffxivbot.models import *
from channels.layers import get_channel_layer 
from asgiref.sync import async_to_sync
chats = ChatMessage.objects.filter(timestamp__lt=time.time()-600)
for chat in chats:
    chat.delete()

