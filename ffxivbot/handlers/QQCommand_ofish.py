from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import time
import datetime
import math

# Modified from http://fish.senriakane.com/ocean.html
def QQCommand_ofish(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        try:
            count = int(receive["message"].replace("/ofish", ""))
        except:
            count = 3
        # fmt: off
        pattern = [1,4,2,5,3,6,1,4,2,5,3,6,
                   4,1,5,2,6,3,4,1,5,2,6,3,
                   2,5,3,6,1,4,2,5,3,6,1,4,
                   5,2,6,3,4,1,5,2,6,3,4,1,
                   3,6,1,4,2,5,3,6,1,4,2,5,
                   6,3,4,1,5,2,6,3,4,1,5,2]
        routeName = ["梅尔夜晚", "梅尔白天", "梅尔黄昏", "罗塔夜晚", "罗塔白天", "罗塔黄昏"]
        routeComment = ["海龙成就 + ※珊瑚蝠鲼", "章鱼成就", "※索蒂斯 + ※依拉丝莫龙", "※索蒂斯 + ※石骨鱼", "水母成就 + 冲分推荐", "鲨鱼成就 + ※珊瑚蝠鲼"]
        routeComment2 = ["", "1区可冲分,追梦失败转成就车", "1区可以冲水母成就", "2区可以冲海龙成就", "", "可以和鲨鱼队一起冲分"]
        schedules = ["梅尔托尔海峡南(夜)-加拉迪翁湾外海(日)-梅尔托尔海峡北(夕)",
                     "梅尔托尔海峡南(日)-加拉迪翁湾外海(夕)- 梅尔托尔海峡北(夜)",
                     "梅尔托尔海峡南(夕)-加拉迪翁湾外海(夜)- 梅尔托尔海峡北(日)",
                     "加拉迪翁湾外海(夜)-梅尔托尔海峡南(日)- 罗塔诺海海面(夕)",
                     "加拉迪翁湾外海(日)-梅尔托尔海峡南(夕)- 罗塔诺海海面(夜)",
                     "加拉迪翁湾外海(夕)-梅尔托尔海峡南(夜)- 罗塔诺海海面(日)"]
        # fmt: on
        offset = 20
        date = datetime.datetime.now()
        last_time = datetime.datetime.now().strftime("%Y-%m-%d 22:15:00")
        if str(date) < str(last_time):
            t = (date - datetime.timedelta(days=1)).strftime("%Y-%m-%d 16:00:00")
        else:
            t = date.strftime("%Y-%m-%d 16:00:00")
        ts = int(time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S")))
        selectedTwoHourChunk = math.floor(ts / (60 * 60 * 2))
        tempTime = (selectedTwoHourChunk + offset) % 72
        i = 0
        num = 0
        route = ""
        rName = []
        while i < 12:
            if tempTime + i >= 72:
                temp = tempTime + i - 72
            else:
                temp = tempTime + i
            temppoop = datetime.datetime.fromtimestamp(
                (selectedTwoHourChunk + i + 4) * (60 * 60 * 2)
            )
            i += 1
            if str(date) < str(temppoop.strftime("%Y-%m-%d %H:15")) and num < count:
                route += (
                    "时间："
                    + temppoop.strftime("%Y-%m-%d %H:%M")
                    + "--航线："
                    + routeName[pattern[temp] - 1]
                    + "\n说明："
                    + routeComment[pattern[temp] - 1]
                    + "     备注："
                    + routeComment2[pattern[temp] - 1]
                    + "\n行程："
                    + schedules[pattern[temp] - 1]
                    + "\n"
                )
                rName.append(routeName[pattern[temp] - 1])
                route += "\n"
                num += 1
        first_time = datetime.datetime.now().strftime("%Y-%m-%d 18:15:00")
        if str(date) > str(first_time) or count > num:
            t = date.strftime("%Y-%m-%d 16:00:00")
            ts = int(time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S")))
            selectedTwoHourChunk = math.floor(ts / (60 * 60 * 2))
            tempTime = (selectedTwoHourChunk + offset) % 72
            i = 0
            while i < 12:
                if tempTime + i >= 72:
                    temp = tempTime + i - 72
                else:
                    temp = tempTime + i
                temppoop = datetime.datetime.fromtimestamp(
                    (selectedTwoHourChunk + i + 4) * (60 * 60 * 2)
                )
                i += 1
                if num < count:
                    route += (
                        "时间："
                        + temppoop.strftime("%Y-%m-%d %H:%M")
                        + "--航线："
                        + routeName[pattern[temp] - 1]
                        + "\n说明："
                        + routeComment[pattern[temp] - 1]
                        + "     备注："
                        + routeComment2[pattern[temp] - 1]
                        + "\n行程："
                        + schedules[pattern[temp] - 1]
                        + "\n"
                    )
                    rName.append(routeName[pattern[temp] - 1])
                    route += "\n"
                    num += 1
        last_msg = route[:-1]
        reply_action = reply_message_action(receive, last_msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, last_msg))
        logging.error(e)
    return action_list
