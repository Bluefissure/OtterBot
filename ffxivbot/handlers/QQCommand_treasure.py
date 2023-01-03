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
import math
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
    try:
        theight, twidth = template.shape[:2]
        result = cv2.matchTemplate(target,template,cv2.TM_CCOEFF_NORMED)
        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
        return min_val
    except Exception as e:
        traceback.print_exc()
    return float("inf")

def img_diff2(target, template):
    def dhash(image):
        resize_height, resized_width = 32, 33
        resized_img = cv2.resize(image, (resized_width, resize_height))
        grey_resized_img = cv2.cvtColor(resized_img, cv2.COLOR_RGB2GRAY)
        hash_list = []
        for row in range(resize_height):
            for col in range(resized_width - 1):
                if grey_resized_img[row, col] > grey_resized_img[row, col + 1]:
                    hash_list.append('1')
                else:
                    hash_list.append('0')
        return '' . join(hash_list)
    def hamming_distance(dhash1, dhash2):
        return bin(int(dhash1, base = 2) ^ int(dhash2, base = 2)).count('1')
    return hamming_distance(dhash(target), dhash(template))

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
        receive = kwargs["receive"]

        # if int(receive["user_id"])!=306401806:
        #     msg = "功能暂时关闭中"
        #     reply_action = reply_message_action(receive, msg)
        #     action_list.append(reply_action)
        #     return action_list

        receive_msg = receive["message"].replace("/treasure", "", 1).strip()
        msg_list = receive_msg.split(" ")
        second_command = msg_list[0]
        if second_command == "" or second_command == "help":
            msg = "藏宝图查询：\n/treasure $image : 查询$image\nPS:截图请截到上下黑边,不要超过黑边."
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
                    diff = img_diff2(target, template)
                    # rev_diff = img_diff(template, target)
                    # diff = min(rev_diff, diff)
                    print("diff with {}: {}".format(treasure_map, diff))
                    if min_diff == -1 or diff < min_diff:
                        min_diff = diff
                        min_treasuremap = treasure_map
                    if max_diff == -1 or diff > max_diff:
                        max_diff = diff
                        max_treasuremap = treasure_map
                if math.isinf(min_diff):
                    msg = "图片匹配失败"
                # elif (not min_treasuremap) or (max_diff > 0.25):
                #     msg = "未查询到有效藏宝图"
                else:
                    territory = min_treasuremap.territory
                    pos_x, pos_y = json.loads(min_treasuremap.position)
                    map_url = "https://map.wakingsands.com/#f=mark&x={}&y={}&id={}".format(pos_x, pos_y, territory.mapid)
                    map_cq = "[CQ:image,file=base64://{}]\n".format(min_treasuremap.uri.replace("data:image/jpeg;base64,", ""))
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
