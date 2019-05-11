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
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename="log/crawl_live.log")


def crawl_json(liveuser):
    jinfo = {
        "title": "Platform not support",
        "image": "https://xn--v9x.net/static/dist/img/tata.jpg",
        "status": "offline"
    }
    platform = liveuser.platform
    if platform=="bilibili":
        try:
            url = r'http://api.live.bilibili.com/AppRoom/index?platform=android&room_id={}'.format(liveuser.room_id)
            s = requests.get(url=url)
            jres = json.loads(s.text)
            if(jres.get("code") == 0):
                jdata = jres.get("data", None)
                jinfo = {
                    "title": jdata.get("title"),
                    "image": jdata.get("face"),
                    "status": jdata.get("status","offline").lower()
                }
                return jinfo
        except:
            logging.error("Error at parsing bilibili API")
            print("Error at parsing bilibili API")
    elif platform=="douyu":
        try:
            url = r'http://open.douyucdn.cn/api/RoomApi/room/{}'.format(liveuser.room_id)
            s = requests.get(url=url)
            jres = json.loads(s.text)
            if(jres.get("error") == 0):
                jdata = jres.get("data", None)
                room_status = jdata.get("room_status", 2)
                jinfo = {
                    "title": jdata.get("room_name"),
                    "image": jdata.get("avatar"),
                    "status": "live" if room_status == "1" else room_status
                }
                return jinfo
        except:
            logging.error("Error at parsing douyu API")
            print("Error at parsing douyu API")
    return jinfo


def crawl_live(liveuser, push=False):
    jinfo = crawl_json(liveuser)
    print(jinfo)
    live_status = jinfo.get("status")
    liveuser.info = json.dumps(jinfo)
    liveuser.last_update_time = int(time.time())
    if live_status!="live":
        for group in liveuser.subscribed_by.all():
            group.pushed_live.clear()
    pushed_group = set()
    if push and str(liveuser.status).lower()!="live" and live_status=="live":
        for bot in QQBot.objects.all():
            group_id_list = [int(item["group_id"]) for item in json.loads(bot.group_list)]
            for group in liveuser.subscribed_by.filter(live_subscription_trigger_time=-1):
                if int(group.group_id) not in group_id_list:
                    continue
                if (group.pushed_live.filter(name=liveuser.name, room_id=liveuser.room_id, platform=liveuser.platform).exists()):
                    continue
                # if (group.group_id) in pushed_group:
                #     continue
                # print(group)
                msg = liveuser.get_share(mode="text")
                jdata = {
                    "action": "send_group_msg",
                    "params": {"group_id": int(group.group_id), "message": msg},
                    "echo": "",
                }
                if not bot.api_post_url:
                    # print("pushing")
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event", "text": json.dumps(jdata),})
                else:
                    url = os.path.join(bot.api_post_url, "{}?access_token={}".format(jdata["action"], bot.access_token))
                    headers = {'Content-Type': 'application/json'} 
                    r = requests.post(url=url, headers=headers, data=json.dumps(jdata["params"]))
                    if r.status_code!=200:
                        logging.error(r.text)
                group.pushed_live.add(liveuser)
                pushed_group.add(group.group_id)
    liveuser.status = live_status
    liveuser.save()
    logging.info("crawled {}".format(liveuser))


def crawl():
    lus = LiveUser.objects.all()
    for lu in lus:
        logging.info("Begin crawling {}".format(lu))
        try:
            crawl_live(lu, True)
        except Exception as e:
            logging.error(e)
        time.sleep(1)
        logging.info("Crawl {} finish".format(lu))


if __name__ == "__main__":
    print("Crawling Live Service Start, check log file log/crawl_live.log")
    while True:
        try:
            crawl()
        except BaseException:
            logging.error("Error")
        time.sleep(60)
