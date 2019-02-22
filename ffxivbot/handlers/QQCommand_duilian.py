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
import time
import traceback


def get_xialian(shanglian):
    url = 'https://duilian.msra.cn/app/CoupletsWS_V2.asmx/GetXiaLian'
    data = {"shanglian":shanglian,"xialianLocker":"0"*len(shanglian),"isUpdate":False}
    r = requests.post(url=url,data=json.dumps(data), headers={'Content-Type': 'application/json'}, timeout=15)
    # print(r.text)
    jres = json.loads(r.text)
    if "d" in jres.keys():
        sets = jres["d"]["XialianSystemGeneratedSets"]
        set_idx = random.randint(0,len(sets)-1)
        xialian = sets[set_idx]["XialianCandidates"]
        xialian = xialian[random.randint(0,len(xialian)-1)]
        return xialian

def get_hengpi(shanglian, xialian):
    url = 'https://duilian.msra.cn/app/CoupletsWS_V2.asmx/GetHengPi'
    data = {"shanglian":shanglian, "xialian":xialian}
    r = requests.post(url=url,data=json.dumps(data), headers={'Content-Type': 'application/json'}, timeout=15)
    # print(r.text)
    jres = json.loads(r.text)
    if "d" in jres.keys():
        sets = jres["d"]
        hengpi = sets[random.randint(0,len(sets)-1)]
        return hengpi

def QQCommand_duilian(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        FF14WIKI_API_URL = global_config["FF14WIKI_API_URL"]
        FF14WIKI_BASE_URL = global_config["FF14WIKI_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        bot = kwargs["bot"]
        if(time.time() < bot.api_time + bot.long_query_interval):
            msg = "技能冷却中"
        else:
            message_content = receive["message"].replace('/duilian','',1).strip()
            msg = "default msg"
            if message_content.find("help")==0 or message_content=="":
                msg = "/duilian $shanglian : 生成$shanglian的下联\n" + \
                        "Powered by https://duilian.msra.cn"
            else:
                shanglian = message_content
                xialian = get_xialian(shanglian)
                if shanglian and xialian:
                    hengpi = get_hengpi(shanglian, xialian)
                msg = "{}\n{}\n{}".format(shanglian, xialian, hengpi)

        if type(msg)==str:
            msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        logging.error(e)
        traceback.print_exc()