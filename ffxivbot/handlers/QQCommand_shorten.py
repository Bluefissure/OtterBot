import sys
import os
from django.db import DatabaseError, transaction
from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import re
import codecs
import copy
from bs4 import BeautifulSoup
import traceback
import base64
import time
from hashlib import sha1
import hmac
import urllib.parse

def get_image_from_CQ(CQ_text):
    if "url=" in CQ_text:
        tmp = CQ_text
        tmp = tmp[tmp.find("url=") : -1]
        tmp = tmp.replace("url=", "")
        img_url = tmp.replace("]", "")
        return img_url
    return None

def shorten(raw_url, **kwargs):
    WEIBO_TOKEN = kwargs.get("WEIBO_TOKEN")
    WEIBO_SHORTEN_SAFEURL = kwargs.get("WEIBO_SHORTEN_SAFEURL")
    long_url = "{}?link={}".format(WEIBO_SHORTEN_SAFEURL, urllib.parse.quote(raw_url.strip()))
    url = "https://api.weibo.com/2/short_url/shorten.json"
    data = {
        "access_token": WEIBO_TOKEN,
        "url_long": long_url,
    }
    r = requests.get(url=url, params=data, timeout=5)
    r_json = r.json()
    if r_json.get("error", None):
        return r_json.get("error", "default error")
    else:
        short_url = r_json["urls"][0].get("url_short", "None")
        return short_url
    return "Unkown Error"

@transaction.atomic
def QQCommand_shorten(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        WEIBO_TOKEN = global_config.get("WEIBO_TOKEN", None)
        WEIBO_SHORTEN_SAFEURL = global_config.get("WEIBO_SHORTEN_SAFEURL", None)
        TIMEFORMAT_MDHMS = global_config.get("TIMEFORMAT_MDHMS")
        ADMIN_ID = global_config.get("ADMIN_ID", "10000")
        action_list = []
        receive = kwargs["receive"]
        msg = "weibo share testing"
        raw_para = receive["message"].replace("/shorten","",1)
        para_segs = raw_para.split(" ")
        while "" in para_segs:
            para_segs.remove("")
        para_segs = list(map(lambda x:x.strip(), para_segs))
        bot = kwargs["bot"]
        if int(receive["user_id"]) != int(ADMIN_ID):
            msg = "仅管理员能够使用此功能"
        else:
            if time.time() < bot.api_time + bot.long_query_interval:
                msg = "技能冷却中"
            else:
                msg = shorten(raw_para, 
                        WEIBO_TOKEN = WEIBO_TOKEN,
                        WEIBO_SHORTEN_SAFEURL=WEIBO_SHORTEN_SAFEURL
                    )
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
