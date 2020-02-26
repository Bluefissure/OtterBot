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
from logging.handlers import TimedRotatingFileHandler
import traceback
from bs4 import BeautifulSoup
from channels.layers import get_channel_layer
from django.db import connection, connections

logging.basicConfig(
                level = logging.INFO,
                format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                handlers = {
                        TimedRotatingFileHandler(
                                        "log/crawl_wb.log",
                                        when="D",
                                        backupCount = 10
                                    )
                        }
            )


def progress(percent, width=50):
    if percent >= 100:
        percent = 100
    show_str = ('[%%-%ds]' % width) % (int(width * percent / 100) * "#")
    print('\r%s %d%%' % (show_str, percent), end='')


def crawl_wb(weibouser, push=False):
    uid = weibouser.uid
    containerid = weibouser.containerid
    url = r'https://m.weibo.cn/api/container/getIndex?type=uid&value={}&containerid={}'.format(uid, containerid)
    s = requests.post(url=url, timeout = 15)
    jdata = json.loads(s.text)
    if(jdata["ok"] == 1):
        for tile in jdata["data"]["cards"]:
            if(len(WeiboTile.objects.filter(itemid=tile.get("itemid", ""))) > 0):
                # print("crawled {} of {} before, pass".format(tile["itemid"], tile["itemid"]))
                continue
            t = WeiboTile(itemid=tile.get("itemid", ""))
            t.owner = weibouser
            t.content = json.dumps(tile)
            t.crawled_time = int(time.time())
            if(tile.get("itemid", "") == ""):
                logging.info("pass a tile of {} cuz empty itemid".format(t.owner))
                # logging.info(json.dumps(tile))
                continue
            channel_layer = get_channel_layer()

            groups = weibouser.subscribed_by.all()
            # print("ready to push groups:{}".format(list(groups)))
            bots = QQBot.objects.all()
            t.save()
            for group in groups:
                for bot in bots:
                    group_id_list = [item["group_id"] for item in json.loads(bot.group_list)] if json.loads(bot.group_list) else []
                    if int(group.group_id) not in group_id_list: continue
                    try:
                        msg = get_weibotile_share(t, mode="text")
                        if bot.share_banned:
                            content_json = json.loads(t.content)
                            mblog = content_json["mblog"]
                            bs = BeautifulSoup(mblog["text"],"html.parser")
                            if "original_pic" in mblog.keys():
                                text = "{}\n{}\n{}".format(
                                                "{}\'s Weibo:\n========".format(t.owner),
                                                bs.get_text().replace("\u200b", "").strip(),
                                                content_json["scheme"]
                                            )
                                msg = [
                                    {
                                        "type": "text",
                                        "data": {
                                            "text": text
                                        },
                                    },
                                    {
                                        "type": "image",
                                        "data": {
                                            "file": mblog["original_pic"]
                                        },
                                    }
                                ]
                            else:
                                msg = "{}\n{}\n{}".format(
                                    "{}\'s Weibo:\n========".format(t.owner),
                                    bs.get_text().replace("\u200b", "").strip(),
                                    content_json["scheme"]
                                )
                        logging.info("Pushing {} to group: {}".format(t, group))
                        # print("msg: {}".format(msg))
                        if push:
                            t.pushed_group.add(group)
                            jdata = {
                                "action": "send_group_msg",
                                "params": {"group_id": int(group.group_id), "message": msg},
                                "echo": "",
                            }
                            if not bot.api_post_url:
                                async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event", "text": json.dumps(jdata), })
                            else:
                                url = os.path.join(bot.api_post_url, "{}?access_token={}".format(jdata["action"], bot.access_token))
                                headers = {'Content-Type': 'application/json'}
                                r = requests.post(url=url, headers=headers, data=json.dumps(jdata["params"]), timeout=5)
                                if r.status_code!=200:
                                    logging.error(r.text)
                    except requests.ConnectionError as e:
                        logging.error("Pushing {} to group: {} ConnectionError".format(t, group))
                    except requests.ReadTimeout as e:
                        logging.error("Pushing {} to group: {} timeout".format(t, group))
                    except Exception as e:
                        traceback.print_exc()
                        logging.error("Error at pushing crawled weibo to {}: {}".format(group, e))

            logging.info("crawled {} of {}".format(t.itemid, t.owner))
    else:
        logging.error("Error at crawling weibo:{}".format(jdata.get("ok", "NULL")))
    return


def crawl():
    wbus = WeiboUser.objects.all()
    for wbu in wbus:
        logging.info("Begin crawling {}".format(wbu.name))
        try:
            crawl_wb(wbu, True)
        except requests.ReadTimeout as e:
            logging.error("crawling {} timeout".format(wbu.name))
        except Exception as e:
            traceback.print_exc()
            logging.error(e)
        time.sleep(1)
        logging.info("Crawl {} finish".format(wbu.name))


if __name__ == "__main__":
    print("Crawling Weibo Service Start, check log file log/crawl_wb.log")
    while True:
        try:
            crawl()
        except BaseException:
            logging.error("Error")
        time.sleep(60)
