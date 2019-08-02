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
    url = "http://gs.choviwu.top/garbage/getGarbage?garbageName={}".format(name)
    r = requests.get(url=url, timeout=5)
    msg = "我也不知道\"{}\"是什么垃圾，再问拉黑了".format(name)
    if r.status_code==200:
        try:
            r_json = r.json()
            if r_json.get("code", -1)==200:
                jdata = r_json.get("data", [])[0]
                gName = jdata.get("gName", "")
                gType = jdata.get("gType", "")
                if not gType.endswith("垃圾"):
                    gType += "垃圾"
                msg = "\"{}\"是{}".format(gName, gType)
        except IndexError as e:
            print("IndexError: {}".format(type(e)))
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
