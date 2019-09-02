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
import traceback
import feedparser
from channels.layers import get_channel_layer
from django.db import connection, connections
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', filename="log/crawl_live.log")


def crawl_json(liveuser):
    platform = liveuser.platform
    if platform == "bilibili":
        try:
            url = r'https://rsshub.app/bilibili/live/room/{}'.format(liveuser.room_id)
            jres = feedparser.parse(url)
            if jres.entries:
                item = jres.entries[0]
                info_s = requests.get("https://api.live.bilibili.com/live_user/v1/UserInfo/get_anchor_in_room?roomid={}".format(liveuser.room_id))
                info_s = info_s.json()
                face_url = ""
                name = ""
                if info_s.get("code", -1) == 0:
                    face_url = info_s["data"]["info"]["face"]
                    name = info_s["data"]["info"]["uname"]
                jinfo = {
                    "title": re.sub(r" \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", "", item.get("title")),
                    "status": "live"
                }
                if face_url: jinfo.update({"image": face_url})
                if name: jinfo.update({"name": name})
                # print(jinfo)
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
            url = r'http://open.douyucdn.cn/api/RoomApi/room/{}'.format(liveuser.room_id)
            s = requests.get(url=url, timeout=5)
            jres = s.json()
            if not isinstance(jres, dict):
                print("jres:{}".format(jres))
            if(jres.get("error") == 0):
                jdata = jres.get("data", None)
                room_status = jdata.get("room_status", 2)
                jinfo = {
                    "title": jdata.get("room_name"),
                    "image": jdata.get("avatar"),
                    "status": "live" if room_status == "1" else room_status,
                    "name": jdata.get("owner_name")
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
    print("jinfo:{}".format(json.dumps(jinfo)))
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
            group_id_list = [int(item["group_id"]) for item in json.loads(bot.group_list)]
            for group in liveuser.subscribed_by.all():
                try:
                    if int(group.group_id) not in group_id_list:
                        continue
                    if (group.pushed_live.filter(name=liveuser.name, room_id=liveuser.room_id, platform=liveuser.platform).exists()):
                        continue
                    # if (group.group_id) in pushed_group:
                    #     continue
                    # print(group)
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
                        r = requests.post(url=url, headers=headers, data=json.dumps(jdata["params"]))
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
