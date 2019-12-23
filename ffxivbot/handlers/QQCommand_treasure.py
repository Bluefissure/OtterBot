from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import traceback
import time
import copy
import base64
import cv2
import numpy as np
from bs4 import BeautifulSoup


def get_image_from_CQ(CQ_text):
    if "url=" in CQ_text:
        tmp = CQ_text
        tmp = tmp[tmp.find("url=") : -1]
        tmp = tmp.replace("url=", "")
        img_url = tmp.replace("]", "")
        return img_url
    return None

def img_diff(target, template):
    theight, twidth = template.shape[:2]
    result = cv2.matchTemplate(target,template,cv2.TM_SQDIFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    return min_val

def read_uri(uri):
    encoded_data = uri.split(',')[1]
    nparr = np.fromstring(base64.b64decode(encoded_data), np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img


def QQCommand_treasure(*args, **kwargs):
    action_list = []
    try:
        # print("begin treasure ==============")
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        receive = kwargs["receive"]

        receive_msg = receive["message"].replace("/treasure", "", 1).strip()
        msg_list = receive_msg.split(" ")
        second_command = msg_list[0]
        if second_command == "" or second_command == "help":
            msg = "藏宝图查询：\n/treasure $image : 查询$image\n"
        else:
            while "" in msg_list:
                msg_list.remove("")
            CQ_text = msg_list[0].strip()
            img_url = get_image_from_CQ(CQ_text)
            if not img_url:
                msg = "未发现图片信息"
            else:
                res = requests.get(url=img_url, timeout=5)
                template_uri = "data:" + res.headers['Content-Type'] + ";" +"base64," + base64.b64encode(res.content).decode("utf-8")
                template = read_uri(template_uri)
                min_diff = -1
                min_treasuremap = None
                max_diff = -1
                max_treasuremap = None
                for treasure_map in TreasureMap.objects.all():
                    target_uri = treasure_map.uri
                    target = read_uri(target_uri)
                    diff = img_diff(target, template)
                    # print("diff with {}: {}".format(treasure_map, diff))
                    if min_diff == -1 or diff < min_diff:
                        min_diff = diff
                        min_treasuremap = treasure_map
                    if max_diff == -1 or diff > max_diff:
                        max_diff = diff
                        max_treasuremap = treasure_map
                if (not min_treasuremap) or (max_diff > 0.25):
                    msg = "未查询到有效藏宝图"
                else:
                    territory = min_treasuremap.territory
                    pos_x, pos_y = json.loads(min_treasuremap.position)
                    map_url = "https://map.wakingsands.com/#f=mark&x={}&y={}&id={}".format(pos_x, pos_y, territory.mapid)
                    msg = "地图：{} 编号：{} 坐标：({}, {})\n{}".format(territory, min_treasuremap.number, pos_x, pos_y, map_url)
                    msg = "[CQ:at,qq={}] ".format(receive["user_id"]) + msg
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc()
    return action_list
