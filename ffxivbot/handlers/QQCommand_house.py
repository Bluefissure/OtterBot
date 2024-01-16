from .QQEventHandler import QQEventHandler
from .QQUtils import *
from .QQCommand_market import handle_server_name_abbr
from ffxivbot.models import QQUser, Server
from difflib import SequenceMatcher
import logging
from datetime import datetime, timedelta
import traceback
import requests
import time
import re
from bs4 import BeautifulSoup


AREA_NAME_ID = {
    "海雾村": 0,
    "海": 0,
    "薰衣草苗圃": 1,
    "森": 1,
    "高脚孤丘": 2,
    "沙": 2,
    "白银乡": 3,
    "白": 3,
    "穹顶皓天": 4,
    "雪": 4,
}

AREA_ID_NAME = {v: k for k, v in AREA_NAME_ID.items()}

SIZE_ID_MAP = {
    0: "S",
    1: "M",
    2: "L",
}

SIZE_NAME_ID_MAP = {
    "S": 0,
    "小": 0,
    "M": 1,
    "中": 1,
    "L": 2,
    "大": 2,
}

STATE_ID_MAP = {
    0: "即将开始",
    1: "可供购买",
    2: "结果公示阶段",
    3: "准备中",
}

REGION_TYPE_ID_MAP = {
    "部队": 1,
    "个人": 2,
}

REGION_TYPE_NAME_MAP = {v: " "  + k for k, v in REGION_TYPE_ID_MAP.items()}

def strftime(sometime):
    if isinstance(sometime, str) or isinstance(sometime, float):
        sometime = int(sometime)
    if isinstance(sometime, int):
        date = datetime.fromtimestamp(sometime)
    elif isinstance(sometime, datetime):
        date = sometime
    return date.strftime("%Y-%m-%d %H:%M:%S")

SOME_ROUND_ENDING = 1705071600

def get_round_ending():
    now_time = time.time()
    if now_time < SOME_ROUND_ENDING:
        return SOME_ROUND_ENDING
    ending = SOME_ROUND_ENDING
    while ending + 86400 * 9 < now_time:
        ending += 86400 * 9
    return ending


def textlize_house_data(house_data, show_area=True):
    area = AREA_ID_NAME.get(house_data["Area"], "未知区域")
    size = SIZE_ID_MAP.get(house_data["Size"], "未知大小")
    p_type = house_data["PurchaseType"]
    r_type = REGION_TYPE_NAME_MAP.get(house_data["RegionType"], "")
    if p_type == 1:
        p_text = "{}g 先到先得".format(house_data["Price"])
    elif p_type == 2:
        state_id = int(house_data["State"])
        round_ending = get_round_ending()
        participate_ending = round_ending - 86400 * 4
        round_starting = round_ending - 86400 * 9
        state_text = STATE_ID_MAP.get(state_id, "未知")
        now_time = time.time()
        if state_id == 0:
            first_seen = int(house_data["FirstSeen"])
            # last_seen = int(house_data["LastSeen"])
            if now_time < participate_ending:  # should not happen
                state_text = "火热抽签中 ({} 结束)".format(strftime(participate_ending))
            else:
                if first_seen <= round_starting:
                    state_text = "结果公示中"
                else:
                    state_text = "等待开始中 (预计 {})".format(strftime(round_ending))
        elif state_id == 1:
            if now_time > participate_ending:
                state_text = "结果公示中"
            else:
                state_text = "火热抽签中 ({}人预约, {} 结束)".format(
                    house_data["Participate"], strftime(participate_ending))
        p_text = "{}g\n{}".format(house_data["Price"], state_text)
        # p_text = "{} {}g".format(state_text, house_data["Price"])
        # p_text += " {} {}".format(strftime(house_data["FirstSeen"]), strftime(house_data["LastSeen"]))
    house_text = "{} {:02d}-{:02d} {}{} {}".format(
        area,
        house_data["Slot"] + 1,
        house_data["ID"],
        size,
        r_type,
        p_text,
    )
    return house_text

def filter_func(area, size, r_type):
    area_ids = []
    for area_name in AREA_NAME_ID.keys():
        if area_name in area:
            area_ids.append(AREA_NAME_ID[area_name])
    size_ids = [SIZE_NAME_ID_MAP[s] for s in size if s in SIZE_NAME_ID_MAP]
    r_type = r_type.lower()
    def _filter(house):
        if area_ids and int(house["Area"]) not in area_ids:
            return False
        if size_ids and int(house["Size"]) not in size_ids:
            return False
        # filter out 2 for 1, filter out 1 for 2
        if r_type != "" and int(house["RegionType"]) + REGION_TYPE_ID_MAP.get(r_type, -1) == 3:
            return False
        return True
    return _filter

def get_house_data(server, area="", size="", r_type=""):
    try:
        server_id = int(server)
    except ValueError:
        server_name = handle_server_name_abbr(server)
        servers = Server.objects.filter(name=server_name)
        if not servers.exists():
            return "服务器名称错误"
        server_id = servers[0].worldId
    url = "https://house.ffxiv.cyou/api/sales?server={}".format(server_id)
    r = requests.get(url, timeout=15, headers={"User-Agent": "OtterBot/1.0 <bluefissure@foxmail.com>"})
    if r.status_code != 200:
        return "服务器请求响应错误"
    houses = r.json()
    filtered_houses = filter(filter_func(area, size, r_type), houses)
    msg = "\n".join([textlize_house_data(house) for house in filtered_houses])
    if msg.strip() == "":
        msg = "所查询房屋信息为空，请重试"
    return "服务器{}的房屋查询结果如下:\n".format(server) + msg


def handle_command(command_seg, user, group):
    help_msg = """/house $server ($area) ($size) ($type): 查询 $server 服务器的 $area 区域房源信息
/house upload: 查询如何上传房源信息
例：/house 萌芽池 海雾村 小 部队
Powered by https://house.ffxiv.cyou"""
    msg = help_msg
    command_len = len(command_seg)
    if command_len == 0 or command_seg[0].lower() == "help":
        return msg
    elif command_seg[0].lower() == "upload":
        return "请参考 https://house.ffxiv.cyou/#/about"
    if time.time() < user.last_api_time + 5:
        msg = "[CQ:at,qq={}] 技能冷却中，请勿频繁调用".format(user.user_id)
        return msg
    # server = None
    if command_len < 1 or command_len > 4:
        msg = "参数错误：\n/house $server ($area) ($size): 查询 $server 服务器的 $area ($size) 房屋信息"
        return msg
    server_name = command_seg[0]
    area = command_seg[1] if command_len >= 2 else ""
    size = command_seg[2] if command_len >= 3 else ""
    r_type = ""
    for k in REGION_TYPE_ID_MAP.keys():
        if k in command_seg:
            r_type = k
            break
    msg = get_house_data(server_name, area, size, r_type)
    user.last_api_time = time.time()
    user.save(update_fields=["last_api_time"])
    return msg


def QQCommand_house(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        # return [reply_message_action(receive, "Universalis 服务已宕机")]
        user = QQUser.objects.get(user_id=receive["user_id"])
        group = kwargs.get("group")
        msg = ""
        command_msg = receive["message"].replace("/house", "", 1).strip()
        command_seg = command_msg.split(" ")
        while "" in command_seg:
            command_seg.remove("")
        # print("Receving command from {} in {}".format(bot, group))
        msg = handle_command(command_seg, user, group)
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
