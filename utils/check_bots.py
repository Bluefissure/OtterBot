#!/usr/bin/env python3
import random
import sys
import os
import codecs
import urllib
import base64
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIVBOT.settings'
from FFXIVBOT import settings
import django
import string
from django.db import connection, connections
django.setup()
from ffxivbot.models import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
channel_layer = get_channel_layer()
qqbots = QQBot.objects.all()
for bot in qqbots:
    print("qq:{}channel:{}".format(bot.user_id,bot.api_channel_name))
    if bot.api_channel_name=='':
        continue
    jdata = {
        "action":"get_group_list",
        "params":{},
        "echo":"get_group_list",
    }
    async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})
    jdata = {
        "action":"_get_friend_list",
        "params":{"flat":True},
        "echo":"_get_friend_list",
    }
    async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})
    jdata = {
        "action":"get_version_info",
        "params":{},
        "echo":"get_version_info",
    }
    async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})
