from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
from bs4 import BeautifulSoup
import urllib
import logging
import traceback

def search_trash(name):
    url = "http://trash.lhsr.cn/sites/feiguan/trashTypes_2/TrashQuery.aspx?kw={}".format(name)
    r = requests.get(url=url, timeout=5)
    msg = "我也不知道\"{}\"是什么垃圾，给你简单介绍一下垃圾的分类吧！\n".format(name)
    msg += "可回收物：\n  废纸张、废塑料、废玻璃制品、废金属、废织物等适宜回收、可循环利用的生活废弃物\n"
    msg += "有害垃圾：\n  废电池、废灯管、废药品、废油漆及其容器等对人体健康或自然环境造成潜在危害的生活废弃物\n"
    msg += "湿垃圾：\n  易腐垃圾，是指食物废料、剩餐剩饭、过期食品、瓜皮果核、花卉绿植、中药药渣等生物质生活废弃物\n"
    msg += "干垃圾：\n  其他垃圾，是指除可回收物、有害垃圾、湿垃圾以外的生活废弃物"
    if r.status_code==200:
        try:
            bs = BeautifulSoup(r.text, "html.parser") 
            info = bs.find_all(class_='info')[0]
            msg = "\"{}\"是{}：\n".format(name, info.get_text().strip())
            msg += bs.find_all(class_='kp2')[0].get_text()
            while "\n\n" in msg:
                msg = msg.replace("\n\n", "\n")
            msg = msg.replace("主要包括", "主要包括：")
            msg = msg.replace("投放要求", "投放要求：")
        except IndexError:
            print("IndexError: {}".format(r.text))
    return msg.strip()



def QQCommand_trash(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        FF14WIKI_API_URL = global_config["FF14WIKI_API_URL"]
        FF14WIKI_BASE_URL = global_config["FF14WIKI_BASE_URL"]
        receive = kwargs["receive"]

        name = receive["message"].replace("/trash", "")
        name = name.strip()
        if not name:
            msg = "/trash $name: 搜索$name是什么垃圾\nPowered by http://t.cn/Ai0Wd7jF"
        else:
            msg = search_trash(name)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
