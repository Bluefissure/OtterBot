#!/usr/bin/env python3
import sys
import os
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'FFXIV.settings'
from FFXIV import settings
django.setup()
from ffxivbot.handlers.QQUtils import *
from asgiref.sync import async_to_sync
from ffxivbot.models import *
import re
import json
import time
import requests
import string
import random
import codecs
import urllib
import base64
import logging
from channels.layers import get_channel_layer
from django.db import connection, connections

def del_bot(day=7):
    bots = QQBot.objects.filter(event_time__lt=time.time()-3600*24*day)
    for b in bots:
        images = Image.objects.filter(add_by_bot=b)
        print(f"bot {b} has upload {len(images)} images.")
        for i in images:
            i.add_by_bot = None
            i.save()
        print(f"bot {b} deleted")
        b.delete()


if __name__ == "__main__":
    del_bot()
