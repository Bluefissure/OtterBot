from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import traceback
import time

TIMEFORMAT_MDHMS = ""

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
    "Fog":(10,27),
    "Thunder":(64,81),
    "Heat Wave":(28,45)
}

def checkWeather(weather, unixSeconds):
    chance = calculateForecastTarget(unixSeconds)
    return (EUREKA_SPECIAL_WEATHER[weather][0] <= chance <= EUREKA_SPECIAL_WEATHER[weather][1])

def eurekaWeather(weather, count, TIMEFORMAT_MDHMS):
    unixSeconds = int(time.time())
    weatherStartTime = getWeatherTimeFloor(unixSeconds)
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

def getWeatherID(territory, chance):
    weather_rate = json.loads(territory.weather_rate.rate)
    lrate = 0
    for (weather_id, rate) in weather_rate:
        if lrate <= chance < lrate + rate:
            return weather_id
        lrate += rate

    print("can't find {} chance:{}".format(territory,chance))
    return -1

def getFollowingWeathers(territory, cnt=5):
    unixSeconds = int(time.time())
    weatherStartTime = getWeatherTimeFloor(unixSeconds)
    now_time = weatherStartTime
    weathers = []
    weather_rate = json.loads(territory.weather_rate.rate)
    for i in range(cnt):
        chance = calculateForecastTarget(now_time)
        weather_id = getWeatherID(territory, chance)
        pre_chance  = calculateForecastTarget(now_time - 8 * 175)
        pre_weather_id = getWeatherID(territory, pre_chance)
        print("weather_id:{}".format(weather_id))
        try:
            weather = Weather.objects.get(id=weather_id)
        except Weather.DoesNotExist as e:
            raise e
        try:
            pre_weather = Weather.objects.get(id=pre_weather_id)
        except Weather.DoesNotExist as e:
            raise e

        weathers.append({
            "pre_name":"{}".format(pre_weather),
            "name":"{}".format(weather),
            "ET":"{}:00".format(getEorzeaHour(now_time)),
            "LT":"{}".format(time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time))),
            })
        now_time += 8 * 175
    return weathers

def getSpecificWeatherTimes(territory, weathers, cnt=5):
    unixSeconds = int(time.time())
    weatherStartTime = getWeatherTimeFloor(unixSeconds)
    count = cnt
    match = 0
    times = []
    weather_rate = json.loads(territory.weather_rate.rate)
    now_time = weatherStartTime
    try_time = 0
    while(match < abs(count) and try_time <= 1000):
        try_time += 1
        chance = calculateForecastTarget(now_time)
        weather_id = getWeatherID(territory, chance)
        pre_chance  = calculateForecastTarget(now_time - 8 * 175)
        pre_weather_id = getWeatherID(territory, pre_chance)
        try:
            pre_weather = Weather.objects.get(id=pre_weather_id)
        except Weather.DoesNotExist as e:
            raise e
        for weather in weathers:
            if weather_id == weather.id:
                times.append({
                    "pre_name":"{}".format(pre_weather),
                    "name":"{}".format(weather),
                    "ET":"{}:00".format(getEorzeaHour(now_time)),
                    "LT":"{}".format(time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time))),
                    })
                match += 1
                break
        now_time += 8 * 175
    return times

def QQCommand_weather(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        global TIMEFORMAT_MDHMS
        TIMEFORMAT_MDHMS = global_config["TIMEFORMAT_MDHMS"]
        action_list = []
        receive = kwargs["receive"]

        if receive["message"].find("/weather eureka")==0:
            # receive_msg = receive["message"].replace("/weather eureka","",1).strip()
            # if receive_msg.find("pzz")==0:
            #     receive_msg = receive_msg.replace("pzz","",1).strip()
            #     try:
            #         cnt = int(receive_msg)
            #     except:
            #         cnt = 3
            #     msg = "接下来Eureka常风之地的强风天气如下：\n%s"%(eurekaWeather("Gale",cnt,TIMEFORMAT_MDHMS))
            # elif receive_msg.find("blizzard")==0:
            #     receive_msg = receive_msg.replace("blizzard","",1).strip()
            #     try:
            #         cnt = int(receive_msg)
            #     except:
            #         cnt = 3
            #     msg = "接下来Eureka恒冰之地的暴雪天气如下：\n%s"%(eurekaWeather("Blizzard",cnt,TIMEFORMAT_MDHMS))
            # elif receive_msg.find("fog")==0:
            #     receive_msg = receive_msg.replace("blizzard","",1).strip()
            #     try:
            #         cnt = int(receive_msg)
            #     except:
            #         cnt = 3
            #     msg = "接下来Eureka恒冰之地的薄雾天气如下：\n%s"%(eurekaWeather("Fog",cnt,TIMEFORMAT_MDHMS))
            # elif receive_msg.find("thunder")==0:
            #     receive_msg = receive_msg.replace("blizzard","",1).strip()
            #     try:
            #         cnt = int(receive_msg)
            #     except:
            #         cnt = 3
            #     msg = "接下来Eureka恒冰之地的雷电天气如下：\n%s"%(eurekaWeather("Thunder",cnt,TIMEFORMAT_MDHMS))
            # elif receive_msg.find("heat_wave")==0:
            #     receive_msg = receive_msg.replace("blizzard","",1).strip()
            #     try:
            #         cnt = int(receive_msg)
            #     except:
            #         cnt = 3
            #     msg = "接下来Eureka恒冰之地的热浪天气如下：\n%s"%(eurekaWeather("Heat Wave",cnt,TIMEFORMAT_MDHMS))
            # reply_action = reply_message_action(receive, msg)
            # action_list.append(reply_action)
            pass
        
        elif receive["message"].find("/weather")==0:
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
                        weathers = getFollowingWeathers(territory, cnt)
                        msg = "接下来{}的天气情况如下：".format(territory)
                        for item in weathers:
                            msg += "\n{} ET:{}\tLT:{}".format("{}->{}".format(item["pre_name"],item["name"]),item["ET"],item["LT"])
                    else:
                        weather = None
                        try:
                            weather_name = msg_args[1]
                            weathers = Weather.objects.filter(name=weather_name)
                            cnt = min(15, int(msg_args[2])) if len(msg_args)>=3 and str.isdigit(msg_args[2]) else 3
                            times = getSpecificWeatherTimes(territory, weathers, cnt)
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