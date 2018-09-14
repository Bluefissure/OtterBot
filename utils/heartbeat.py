#!/usr/bin/env python3
import random
import sys
import os
import codecs
import urllib
import base64
sys.path.append('/home/ubuntu/FFXIVBOT/')
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIVBOT.settings'
from FFXIVBOT import settings
import django
import string
from django.db import connection, connections
django.setup()
from ffxivbot.models import *
from channels.layers import get_channel_layer 
from asgiref.sync import async_to_sync
import time
channel_layer = get_channel_layer()
qqbots = QQBot.objects.all()
for bot in qqbots:
    print("heartbeating qq:{} channel:{}".format(bot.user_id,bot.api_channel_name))
    if(int(time.time()) > bot.api_time+59 and int(time.time()) < bot.event_time+24*3600):
        if bot.api_channel_name=='':
            print("passing empty api channel for qq:{}".format(bot.user_id))
            continue
        jdata = {
            "action":"get_status",
            "params":{},
            "echo":"get_status:{}".format(bot.user_id),
        }
        async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})
        print("api heartbeat sent to qq:{}".format(bot.user_id))
    if(int(time.time()) > bot.event_time+59 and int(time.time()) < bot.event_time+24*3600):
        if bot.event_channel_name=='':
            print("passing empty event channel for qq:{}".format(bot.user_id))
            continue
        jdata = {
            "action":"get_status",
            "params":{},
            "echo":"get_status:{}".format(bot.user_id),
        }
        async_to_sync(channel_layer.send)(bot.event_channel_name, {"type": "send.event","text": json.dumps(jdata),})
        print("event heartbeat sent to qq:{}".format(bot.user_id))
