from .QQEventHandler import QQEventHandler
from .QQUtils import *
from .RsshubUtil import RsshubUtil
from ffxivbot.models import *
import logging
import json
import random
import requests
import re
import traceback
from bs4 import BeautifulSoup

def extract_url(text: str):
    try:
        aid = re.compile(r'(av|AV)\d+').search(text)
        bvid = re.compile(r'(BV|bv)([a-zA-Z0-9])+').search(text)
        if bvid:
            url = f'https://api.bilibili.com/x/web-interface/view?bvid={bvid[0]}'
        else:
            url = f'https://api.bilibili.com/x/web-interface/view?aid={aid[0][2:]}'
        return url
    except:
        traceback.print_exc()
    return None

def extract_nn(feed):
    try:
        pattern = r"【FF14\/时尚品鉴】第\d+期 满分攻略"
        for item in feed["items"]:
            if re.match(pattern, item["title"]):
                h = BeautifulSoup(item["summary"], "lxml")
                image = re.sub('https://www.bilibili.com/video/', '', h.img.attrs["src"])
                api_url = extract_url(item["link"])
                r = requests.get(api_url, timeout=3).json()
                text = r['data']['desc']
                text = text.replace("个人攻略网站", "游玩C攻略站")
                res_data = {
                    "url": item["id"],
                    "title": item["title"],
                    "content": text,
                    "image": image,
                }
                return res_data
    except:
        traceback.print_exc()
    return None

def QQCommand_nuannuan(*args, **kwargs):
    action_list = []
    bot = kwargs["bot"]
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        receive = kwargs["receive"]
        try:
            rsshub = RsshubUtil()
            feed = rsshub.biliuservedio(15503317)
            res_data = extract_nn(feed)
            # print("res_data:{}".format(res_data))
            if not res_data:
                feed = rsshub.biliuserdynamic(15503317)
                res_data = extract_nn(feed)
            if not res_data:
                msg = "无法查询到有效数据，请稍后再试"
            else:
                msg = [{"type": "share", "data": res_data}]
                if receive.get("message", "").endswith("image"):
                    res_str = "\n".join([res_data["title"], res_data["content"]])
                    msg = text2img(res_str)
                    msg += res_data["url"]
                # print(msg)
        except Exception as e:
            msg = "Error: {}".format(type(e))
            traceback.print_exc()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
