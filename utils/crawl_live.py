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
from ffxivbot.handlers.RsshubUtil import RsshubUtil
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
from logging.handlers import TimedRotatingFileHandler
import traceback
import feedparser
import socket
from channels.layers import get_channel_layer
from django.db import connection, connections
from bs4 import BeautifulSoup

socket.setdefaulttimeout(5)
logging.basicConfig(
                level = logging.INFO,
                format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers = {
                        TimedRotatingFileHandler(
                                        "log/crawl_live.log",
                                        when = "D",
                                        backupCount = 10
                                    )
                        }
            )


def crawl_json(liveuser):
    platform = liveuser.platform
    rsshub = RsshubUtil()
    if platform == "bilibili":
        try:
            feed = rsshub.live(liveuser.platform, room_id=liveuser.room_id)
            if feed.entries:
                entry = feed.entries[0]
                title = re.sub(r"\d+-\d+-\d+ \d+:\d+:\d+", "", entry.title).strip()
                face_url = ""
                name = feed.feed.title.replace(" 直播间开播状态", "")
                jinfo = {
                    "title": title,
                    "status": "live"
                }
                if face_url: jinfo.update({"image": face_url})
                if name: jinfo.update({"name": name})
            else:
                jinfo = {
                    "status": "offline",
                }
            return jinfo
        except json.decoder.JSONDecodeError as e:
            logging.error("Error at parsing bilibili API to json:{}".format(s.text))
            print("Error at parsing bilibili API to json:{}".format(s.text))
        except Exception as e:
            logging.error("Error at parsing bilibili API")
            print("Error at parsing bilibili API:{}".format(type(e)))
            traceback.print_exc()
    elif platform == "douyu":
        try:
            feed = rsshub.live(liveuser.platform, room_id=liveuser.room_id)
            if feed.entries:
                entry = feed.entries[0]
                title = re.sub(r"\d+-\d+-\d+ \d+:\d+:\d+", "", entry.title).strip()
                face_url = ""
                name = feed.feed.title.replace("的斗鱼直播间", "")
                jinfo = {
                    "title": title,
                    "status": "live"
                }
                if face_url: jinfo.update({"image": face_url})
                if name: jinfo.update({"name": name})
            else:
                jinfo = {
                    "status": "offline",
                }
            return jinfo
        except Exception as e:
            logging.error("Error at parsing douyu API")
            print("Error at parsing douyu API:{}".format(type(e)))
            traceback.print_exc()
    return None


def crawl_live(liveuser, push=False):
    if not liveuser.subscribed_by.exists():
        for group in liveuser.subscribed_by.all():
            group.pushed_live.remove(liveuser)
        logging.info("Skipping {} cuz no subscription".format(liveuser))
        return
    jinfo = crawl_json(liveuser)
    print("{} jinfo:{}".format(liveuser, json.dumps(jinfo)))
    if not jinfo:
        logging.error("Crawling {} failed, please debug the response.".format(liveuser))
        logging.error("jinfo:{}".format(jinfo))
        return
    live_status = jinfo.get("status")
    liveuser.name = jinfo.get("name", liveuser.name)
    liveuser_info = json.loads(liveuser.info)
    liveuser_info.update(jinfo)
    liveuser.info = json.dumps(liveuser_info)
    liveuser.last_update_time = int(time.time())
    if live_status!="live":
        for group in liveuser.subscribed_by.all():
            group.pushed_live.remove(liveuser)
    pushed_group = set()
    if push and live_status=="live":
        for bot in QQBot.objects.all():
            group_id_list = [int(item["group_id"]) for item in json.loads(bot.group_list)] if json.loads(bot.group_list) else []
            for group in liveuser.subscribed_by.all():
                try:
                    if int(group.group_id) not in group_id_list:
                        continue
                    if (group.pushed_live.filter(name=liveuser.name, room_id=liveuser.room_id, platform=liveuser.platform).exists()):
                        continue
                    msg = liveuser.get_share(mode="text")
                    if bot.share_banned:
                        jmsg = liveuser.get_share()
                        msg = "{}\n{}\n{}".format(
                                jmsg.get("title"),
                                jmsg.get("content"),
                                jmsg.get("url")
                            )
                    jdata = {
                        "action": "send_group_msg",
                        "params": {"group_id": int(group.group_id), "message": msg},
                        "echo": "",
                    }
                    if not bot.api_post_url:
                        print("pushing {} to {}".format(liveuser, group.group_id))
                        logging.info("pushing {} to {}".format(liveuser, group.group_id))
                        channel_layer = get_channel_layer()
                        async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event", "text": json.dumps(jdata),})
                    else:
                        url = os.path.join(bot.api_post_url, "{}?access_token={}".format(jdata["action"], bot.access_token))
                        headers = {'Content-Type': 'application/json'}
                        r = requests.post(url=url, headers=headers, data=json.dumps(jdata["params"]), timeout=10)
                        if r.status_code!=200:
                            logging.error(r.text)
                    group.pushed_live.add(liveuser)
                    pushed_group.add(group.group_id)
                except Exception as e:
                    logging.error("Error at pushing crawled live to {}: {}".format(group, e))
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
            print("Error:{}".format(e))
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
