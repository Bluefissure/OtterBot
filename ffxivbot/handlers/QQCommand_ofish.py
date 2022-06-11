from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import math
from datetime import datetime, timedelta

# fmt: off
PATTERN = [
    'BD', 'TD', 'ND', 'RD', 'BS', 'TS', 'NS', 'RS', 'BN', 'TN', 'NN', 'RN',
    'TD', 'ND', 'RD', 'BS', 'TS', 'NS', 'RS', 'BN', 'TN', 'NN', 'RN', 'BD',
    'ND', 'RD', 'BS', 'TS', 'NS', 'RS', 'BN', 'TN', 'NN', 'RN', 'BD', 'TD',
    'RD', 'BS', 'TS', 'NS', 'RS', 'BN', 'TN', 'NN', 'RN', 'BD', 'TD', 'ND',
    'BS', 'TS', 'NS', 'RS', 'BN', 'TN', 'NN', 'RN', 'BD', 'TD', 'ND', 'RD',
    'TS', 'NS', 'RS', 'BN', 'TN', 'NN', 'RN', 'BD', 'TD', 'ND', 'RD', 'BS',
    'NS', 'RS', 'BN', 'TN', 'NN', 'RN', 'BD', 'TD', 'ND', 'RD', 'BS', 'TS',
    'RS', 'BN', 'TN', 'NN', 'RN', 'BD', 'TD', 'ND', 'RD', 'BS', 'TS', 'NS',
    'BN', 'TN', 'NN', 'RN', 'BD', 'TD', 'ND', 'RD', 'BS', 'TS', 'NS', 'RS',
    'TN', 'NN', 'RN', 'BD', 'TD', 'ND', 'RD', 'BS', 'TS', 'NS', 'RS', 'BN',
    'NN', 'RN', 'BD', 'TD', 'ND', 'RD', 'BS', 'TS', 'NS', 'RS', 'BN', 'TN',
    'RN', 'BD', 'TD', 'ND', 'RD', 'BS', 'TS', 'NS', 'RS', 'BN', 'TN', 'NN'
]
# fmt: on

# Bloodbrine Sea (B)  绯汐海航线
BS = [ '谢尔达莱群岛近海', '梅尔托尔海峡北', '绯汐海近海' ]
# Rothlyt Sound (T)   罗斯利特湾航线
TS = [ '谢尔达莱群岛近海', '罗塔诺海海面', '罗斯利特湾近海' ]
# Northern Strait of Merlthor (N)  梅尔托尔海峡北航线
NS = [ '梅尔托尔海峡南', '加拉迪翁湾外海', '梅尔托尔海峡北' ]
# Rhotano Sea (R)     罗塔诺海航线
RS = [ '加拉迪翁湾外海', '梅尔托尔海峡南', '罗塔诺海海面' ]
# (D)(S)(N)
Day = [ '(日)', '(夕)', '(夜)' ]
Sunset = [ '(夕)', '(夜)', '(日)' ]
Night = [ '(夜)', '(日)', '(夕)' ]

_2HR = 2 * 60 * 60 * 1000
_8HR = 8 * 60 * 60 * 1000
OFFSET = 88

def get_route_detail(route: str):
    route_detail = ""
    if route[:1] == "B":
        flag1 = BS
        _route = "绯汐海航线"
    elif route[:1] == "T":
        flag1 = TS
        _route = "罗斯利特湾航线"
    elif route[:1] == "N":
        flag1 = NS
        _route = "梅尔托尔海峡北航线"
    else:
        flag1 = RS
        _route = "罗塔诺海航线"
    if route[-1:] == "D":
        flag2 = Sunset
    elif route[-1:] == "S":
        flag2 = Night
    else:
        flag2 = Day
    for i in range(3):
        route_detail += flag1[i] + flag2[i] + "-"
    return f"航线：{_route}\n行程：{route_detail[:-1]}"

# 往后延一个天气
def get_route_desc(route: str):
    if route == "BN":
        desc = "只有我最鳐摆(成就)"
    elif route == "TN":
        desc = "气鲀四海(成就) ※石骨鱼"
    elif route == "NN":
        desc = "八爪旅人(成就)"
    elif route == "RN":
        desc = "冲分推荐 ※水母狂魔"
    elif route == "BD":
        desc = "横路不通(成就) ※海洋蟾蜍"
    elif route == "TD":
        desc = "气鲀四海(成就) 只有我最鳐摆(成就)"
    elif route == "ND":
        desc = "※索蒂斯 ※依拉丝莫龙"
    elif route == "RD":
        desc = "冲分推荐 捕鲨人(成就) ※珊瑚蝠鲼"
    elif route == "BS":
        desc = "※哈弗古法 ※依拉丝莫龙"
    elif route == "TS":
        desc = "※哈弗古法 ※盾齿龙"
    elif route == "NS":
        desc = "龙马惊神(成就) ※珊瑚蝠鲼"
    elif route == "RS":
        desc = "※索蒂斯 ※石骨鱼"
    return desc

# Data from https://ffxiv.pf-n.co/ocean-fishing/
def QQCommand_ofish(*args, **kwargs):
    action_list = []
    try:
        receive = kwargs["receive"]
        command = receive["message"].replace("/ofish", "").strip()
        if (not command) or command.isdigit():
            command = "3" if not command else command
            count = int(command)
            count = min(count, 5)
            # 初始化数据
            cstTime = datetime.utcnow().timestamp() * 1000 + _8HR
            cstDate = datetime.utcnow() + timedelta(hours=8)
            cstNowHour = cstDate.hour
            if cstNowHour % 2 == 0:
                last_time = cstDate.strftime("%Y-%m-%d %H:15:00")
                flag = 0
            else:
                if cstNowHour < 10:
                    h = f"0{cstNowHour - 1}"
                else:
                    h = cstNowHour - 1
                last_time = cstDate.strftime(f"%Y-%m-%d {h}:15:00")
                flag = 1
            # 查询航班
            msg = ""
            i = 1
            while i <= int(count):
                if cstDate.strftime("%Y-%m-%d %H:%M:%S") > last_time:
                    nextTime = 2 * i
                    voyageNumber = math.floor( ( cstTime + _2HR * i ) / _2HR )
                    route = PATTERN[(OFFSET + voyageNumber) % len(PATTERN)]
                    if flag:
                        t = cstDate + timedelta(hours=nextTime-1)
                        routeTime = f"时间：{t.strftime(f'%Y-%m-%d %H:00')}"
                    else:
                        t = cstDate + timedelta(hours=nextTime)
                        routeTime = f"时间：{t.strftime(f'%Y-%m-%d %H:00')}"
                    msg += f"{routeTime}---{get_route_detail(route)}\n"
                    msg += f"说明：{get_route_desc(route)}\n"
                    i += 1
                else:
                    voyageNumber = math.floor( cstTime / _2HR )
                    route = PATTERN[(OFFSET + voyageNumber) % len(PATTERN)]
                    routeTime = f"时间：{cstDate.strftime(f'%Y-%m-%d {cstNowHour}:00')}"
                    msg += f"{routeTime}---{get_route_detail(route)}\n"
                    msg += f"说明：{get_route_desc(route)}\n"
                    cstDate = cstDate + timedelta(minutes=15)
                msg += "\n"
            last_msg = msg[:-2]
            reply_action = reply_message_action(receive, last_msg)
            action_list.append(reply_action)
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list