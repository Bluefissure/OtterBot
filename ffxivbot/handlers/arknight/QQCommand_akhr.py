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
import base64
import time
from hashlib import sha1
import hmac

def get_image_from_CQ(CQ_text):
    if "url=" in CQ_text:
        tmp = CQ_text
        tmp = tmp[tmp.find("url=") : -1]
        tmp = tmp.replace("url=", "")
        img_url = tmp.replace("]", "")
        return img_url
    return None

def tencent_ocr(img_url, SecretId, SecretKey):
    req_para = {
        "Action":"GeneralBasicOCR",
        "ImageUrl":img_url,
        "Version":"2018-11-19",
        "Region":"ap-beijing",
        "Timestamp":int(time.time()),
        "Nonce":random.randint(1,100000),
        "SecretId":SecretId,
    }
    raw_msg = "&".join(["{}={}".format(kv[0],kv[1]) for kv in sorted(req_para.items(), key=lambda x: x[0])])
    raw_msg = 'GETocr.tencentcloudapi.com/?'+raw_msg
    raw = raw_msg.encode()
    key = SecretKey.encode()
    hashed = hmac.new(key, raw, sha1)
    b64output = base64.encodebytes(hashed.digest()).decode('utf-8')
    req_para.update({
        "Signature":b64output
    })
    r = requests.get(url="https://ocr.tencentcloudapi.com/", params=req_para)
    if r.status_code == 200:
        return r.json()
    return r.text

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


def get_comb_text(hr, all_comb=False):
    msg = ""
    max_comb = 5
    iter_comb = 0
    for comb in hr:
        iter_comb += 1
        if iter_comb > max_comb and not all_comb:    # limit response text length?
            break
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
        action_list = []
        receive = kwargs["receive"]
        akhr_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "akhr.json")
        akhr = json.load(codecs.open(akhr_file,"r","utf8"))
        msg = "akhr testing"
        all_comb = "all" in receive["message"]
        para_segs = receive["message"].replace("/akhr","",1).replace("all","",1).split(" ")
        while "" in para_segs:
            para_segs.remove("")
        if len(para_segs) == 0 or para_segs[0] == "help":
            msg = "/akhr $tag：按照$tag查询罗德岛公开招募（多tag空格分割）"
        else:
            img_url = get_image_from_CQ(" ".join(para_segs))
            msg = ""
            if img_url:
                SecretId = global_config["TENCENT_OCR_SECRETID"]
                SecretKey = global_config["TENCENT_OCR_SECRETKEY"]
                img_text = tencent_ocr(img_url, SecretId, SecretKey)
                if not isinstance(img_text, dict):
                    print(img_text)
                    logging.error(img_text)
                valid_tags = ['女性干员', '费用回复', '资深干员', '医疗干员', '减速', '位移', '特种干员', '治疗', '爆发', '男性干员', '削弱', '近战位', '先锋干员', '支援', '输出', '生存', '召唤', '控场', '防护', '高级资深干员', '群攻', '远程位', '狙击干员', '三测暂不实装', '术师干员', '近卫干员', '新手', '辅助干员', '重装干员', '快速复活']
                tags_list = []
                for text in img_text["Response"]["TextDetections"]:
                    if text["DetectedText"] in valid_tags: 
                        tags_list.append(text["DetectedText"])
                tags_list = list(set(tags_list))
                msg = "OCR识别结果为:{}\n========\n".format(tags_list)
                hr = get_comb(akhr, tags_list)
            else:
                hr = get_comb(akhr, para_segs)
            msg += get_comb_text(hr, all_comb)
            if not msg:
                msg += "找不到符合的结果，请检查输入参数"
            else:
                msg += "\nPowered by: https://bbs.nga.cn/read.php?tid=16971344"
                if img_url:
                    msg += " and https://cloud.tencent.com/product/ocr"

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
