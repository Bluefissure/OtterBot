from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import base64

def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False

def whatanime(receive, WHATANIME_API_URL):
    tmp = receive["message"]
    tmp = tmp[tmp.find("url="):-1]
    tmp = tmp.replace("url=","")
    img_url = tmp.replace("]","")
    logging.debug("getting img_url:%s"%(img_url))
    r = requests.get(img_url,timeout=30)
    imgb64 = base64.b64encode(r.content)
    logging.debug("whatanime post")
    r2 = requests.post(url=WHATANIME_API_URL,data={"image":imgb64.decode()},timeout=30)
    logging.debug("WhatAnime_res:\n%s"%(r2.text))
    if(r2.status_code==200):
        logging.debug("finished whatanime\nParsing.........")
        json_res = json.loads(r2.text)
        if(len(json_res["docs"])==0):
            msg = "未找到所搜索的番剧"
        else:
            anime = json_res["docs"][0]
            title_list = ["title_chinese","title","title_native","anime"]
            title=""
            for item in anime["synonyms_chinese"]:
                if(item!="" and check_contain_chinese(item) and title==""):
                    title = item
                    break
            for item in title_list:
                if(anime[item]!="" and  check_contain_chinese(anime[item])and title==""):
                    title = anime[item]
                    break
            for item in title_list:
                if(anime[item]!="" and title==""):
                    title = anime[item]
                    break

            duration = [(int(anime["from"])//60,int(anime["from"])%60),(int(anime["to"])//60,int(anime["to"])%60)]
            msg = "%s\nEP#%s\n%s:%s-%s:%s\n相似度:%.2f%%"%(title,anime["episode"],duration[0][0],duration[0][1],duration[1][0],duration[1][1],float(anime["similarity"])*100)
            msg = msg+"\nPowered by https://trace.moe/"
    elif (r2.status_code==413):
        msg = "图片太大啦，请压缩至1M"
    else:
        msg = "Error at whatanime API, status code %s"%(r2.status_code)
    return msg


def QQCommand_anime(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        WHATANIME_TOKEN = global_config["WHATANIME_TOKEN"]
        WHATANIME_API_URL = global_config["WHATANIME_API_URL"].format(WHATANIME_TOKEN)
        action_list = []
        receive = kwargs["receive"]

        logging.debug("anime_msg:%s"%(receive["message"]))
        qq = int(receive["user_id"])
        msg = ""
        if ("CQ" in receive["message"] and "url=" in receive["message"]):
            msg = whatanime(receive, WHATANIME_API_URL)
        else:
            msg = "请在命令后添加图片"
        msg = msg.strip()
        if msg:
            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)