import sys
import os
from ..QQEventHandler import QQEventHandler
from ..QQUtils import *
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

def get_hire(akhr, tag_list):
    hr = []
    tag_length = len(tag_list)
    for agent in akhr:
        match = [False]*tag_length
        agent_tags = copy.deepcopy(agent["tags"])
        agent_tags.append("{}干员".format(agent["type"]))
        agent_tags.append("{}性干员".format(agent["sex"]))
        for tag in agent_tags:
            for i in range(tag_length):
                if tag == tag_list[i]:
                    match[i] = True
        if all(match) and not agent["hidden"]:
            if "高级资深干员" in agent_tags:
                if "高级资深干员" in tag_list:
                    hr.append(agent)
            # elif "资深干员" in agent_tags:
            #     if "资深干员" in tag_list:
            #         hr.append(agent)
            else:
                hr.append(agent)
    return sorted(hr, key=lambda x:-x["level"])


def get_comb(akhr, tag_list):
    tag_length = len(tag_list)
    hr3 = []
    for i in range(tag_length):
        for j in range(i+1, tag_length):
            for k in range(j+1, tag_length):
                tags_comb = [tag_list[i], tag_list[j], tag_list[k]]
                hr3.append({
                        " ".join(tags_comb):get_hire(akhr, tags_comb) 
                    })
    hr2 = []
    for i in range(tag_length):
        for j in range(i+1, tag_length):
            tags_comb = [tag_list[i], tag_list[j]]
            hr2.append({
                    " ".join(tags_comb):get_hire(akhr, tags_comb) 
                })
    hr1 = []
    for i in range(tag_length):
        tags_comb = [tag_list[i]]
        hr1.append({
                " ".join(tags_comb):get_hire(akhr, tags_comb) 
            })
    hr = hr3 + hr2 + hr1
    hr = list(filter(lambda x:list(x.values())[0], hr))
    return sorted(hr, key=lambda x: -(list(x.values())[0][-1]["level"]))


def get_comb_text(hr):
    msg = ""
    max_comb = 3
    iter_comb = 0
    for comb in hr:
        iter_comb += 1
        # if iter_comb > max_comb:
        #     break
        comb_name = list(comb.keys())[0]
        comb_agents = list(comb.values())[0]
        msg += "========\n" if iter_comb>1 else "" 
        msg += "{}:\n".format(comb_name)
        for i in range(6,0,-1):
            lv_i = list(filter(lambda x:x["level"]==i, comb_agents))
            if lv_i:
                text = " ".join(list(map(lambda x:x["name"], lv_i)))
                msg += "    {}🌟:{}\n".format(i, text)
    return msg.strip()


def QQCommand_akhr(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        SORRY_BASE_URL = global_config["SORRY_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        sorrygifs = SorryGIF.objects.all()
        akhr_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "akhr.json")
        akhr = json.load(codecs.open(akhr_file,"r","utf8"))
        msg = "akhr testing"
        para_segs = receive["message"].replace("/akhr","",1).split(" ")
        while "" in para_segs:
            para_segs.remove("")
        if len(para_segs) == 0 or para_segs[0] == "help":
            msg = "/akhr $tag：按照$tag查询罗德岛公开招募（多tag空格分割）"
        else:
            hr = get_comb(akhr, para_segs)
            msg = get_comb_text(hr)
            if not msg:
                msg = "找不到符合的结果，请检查输入参数"

        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return []
