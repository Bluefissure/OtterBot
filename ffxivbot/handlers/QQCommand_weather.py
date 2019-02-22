from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import traceback
import time

def QQCommand_weather(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        TIMEFORMAT_MDHMS = global_config["TIMEFORMAT_MDHMS"]
        action_list = []
        receive = kwargs["receive"]

        if receive["message"].find("/weather")==0:
            msg_content = receive["message"].replace("/weather","",1).strip()
            msg_args = msg_content.split(" ")
            territory_name = msg_args[0]
            territory = None
            if len(territory_name)==0 or territory_name=="help":
                msg = "/weather $map ($cnt): 查看对应地图接下来的(几个)天气\n" +\
                    "/weather $map $weather ($cnt): 查看对应地图接下来的(几个)特定天气出现时间"
            else:
                try:
                    territory = Territory.objects.get(name=territory_name)
                except Territory.DoesNotExist:
                    for temp in Territory.objects.all():
                        for temp_name in json.loads(temp.nickname):
                            if temp_name in territory_name or territory_name in temp_name:
                                territory = temp
                                break
                        if territory:
                            break
                if territory:
                    if len(msg_args)==1 or str.isdigit(msg_args[1]):
                        cnt = min(15, int(msg_args[1])) if len(msg_args)>=2 else 5
                        weathers = getFollowingWeathers(territory, cnt, TIMEFORMAT_MDHMS)
                        msg = "接下来{}的天气情况如下：".format(territory)
                        for item in weathers:
                            msg += "\n{} ET:{}\tLT:{}".format("{}->{}".format(item["pre_name"],item["name"]),item["ET"],item["LT"])
                    else:
                        weather = None
                        try:
                            weather_name = msg_args[1]
                            weathers = Weather.objects.filter(name=weather_name)
                            cnt = min(15, int(msg_args[2])) if len(msg_args)>=3 and str.isdigit(msg_args[2]) else 3
                            times = getSpecificWeatherTimes(territory, weathers, cnt, TIMEFORMAT_MDHMS)
                            msg = "接下来{}的{}天气如下：".format(territory, weather_name)
                            for item in times:
                                msg += "\n{} ET:{}\tLT:{}".format("{}->{}".format(item["pre_name"],item["name"]),item["ET"],item["LT"])
                        except Weather.DoesNotExist:
                            msg = "找不到所查询天气：{}".format(msg_args[1])
                else:
                    msg = "找不到所查询区域：{}".format(territory_name)
            if msg:
                if type(msg)==str:
                    msg = msg.strip()
                reply_action = reply_message_action(receive, msg)
                action_list.append(reply_action)

        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)