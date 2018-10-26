from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random
import time

def calculateForecastTarget(unixSeconds): 
    # Thanks to Rogueadyn's SaintCoinach library for this calculation.
    # lDate is the current local time.
    # Get Eorzea hour for weather start
    bell = unixSeconds / 175

    # Do the magic 'cause for calculations 16:00 is 0, 00:00 is 8 and 08:00 is 16
    increment = int(bell + 8 - (bell % 8)) % 24

    # Take Eorzea days since unix epoch
    totalDays = unixSeconds // 4200
    # totalDays = (totalDays << 32) >>> 0; # Convert to uint

    calcBase = totalDays * 100 + increment

    step1 = (((calcBase << 11)%(0x100000000)) ^ calcBase)
    step2 = (((step1 >> 8)%(0x100000000)) ^ step1)
    
    return step2 % 100

def getEorzeaHour(unixSeconds):
    bell = (unixSeconds / 175) % 24;
    return int(bell)

def getWeatherTimeFloor(unixSeconds):
    # Get Eorzea hour for weather start
    bell = (unixSeconds / 175) % 24
    startBell = bell - (bell % 8)
    startUnixSeconds = round(unixSeconds - (175 * (bell - startBell)))
    return startUnixSeconds

EUREKA_SPECIAL_WEATHER = {
    "Gale":(30,59),
    "Blizzard":(82,99),
}

def checkWeather(weather, unixSeconds):
    chance = calculateForecastTarget(unixSeconds)
    return (EUREKA_SPECIAL_WEATHER[weather][0] <= chance <= EUREKA_SPECIAL_WEATHER[weather][1])

def eurekaWeather(weather, count, TIMEFORMAT_MDHMS):
    unixSeconds = int(time.time())
    weatherStartTime = getWeatherTimeFloor(unixSeconds);
    count = min(count,10)
    count = max(count,-10)
    match = 0
    msg = ""
    now_time = weatherStartTime
    tryTime = 0
    while(match < abs(count) and tryTime <= 1000):
        tryTime += 1
        if(checkWeather(weather, now_time)):
            msg += "ET: %s:00\tLT: %s\n"%(getEorzeaHour(now_time),time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)))
            match += 1
        now_time += 8 * 175 if count>=0 else -8 * 175
    return msg.strip()

class QQCommand_weather(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_weather, self).__init__()
    def __call__(self, **kwargs):
        try:
            global_config = kwargs["global_config"]
            QQ_BASE_URL = global_config["QQ_BASE_URL"]
            TIMEFORMAT_MDHMS = global_config["TIMEFORMAT_MDHMS"]
            action_list = []
            receive = kwargs["receive"]

            if receive["message"].find("/weather eureka")==0:
                receive_msg = receive["message"].replace("/weather eureka","",1).strip()
                if receive_msg.find("pzz")==0:
                    receive_msg = receive_msg.replace("pzz","",1).strip()
                    try:
                        cnt = int(receive_msg)
                    except:
                        cnt = 3
                    msg = "接下来Eureka常风之地的强风天气如下：\n%s"%(eurekaWeather("Gale",cnt,TIMEFORMAT_MDHMS))
                elif receive_msg.find("blizzard")==0:
                    receive_msg = receive_msg.replace("blizzard","",1).strip()
                    try:
                        cnt = int(receive_msg)
                    except:
                        cnt = 3
                    msg = "接下来Eureka恒冰之地的暴雪天气如下：\n%s"%(eurekaWeather("Blizzard",cnt,TIMEFORMAT_MDHMS))
                reply_action = self.reply_message_action(receive, msg)
                action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)