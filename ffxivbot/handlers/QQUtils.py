import json
import logging
import io
import os
import re
import time
import traceback
import urllib
import requests
import base64
import random
import math
import difflib
from bs4 import BeautifulSoup
from PIL import ImageFont, ImageDraw
from PIL import Image as PILImage

from ffxivbot.models import *


CAFEMAKER = "https://cafemaker.wakingsands.com"
XIVAPI = "https://xivapi.com"


def reply_message_action(receive, msg):
    action = {"action": "", "params": {}, "echo": ""}
    if receive["message_type"] == "group":
        action.update(
            {
                "action": "send_group_msg",
                "params": {"group_id": receive["group_id"], "message": msg},
            }
        )
    elif receive["message_type"] == "discuss":
        action.update(
            {
                "action": "send_discuss_msg",
                "params": {"discuss_id": receive["discuss_id"], "message": msg},
            }
        )
    else:
        action.update(
            {
                "action": "send_private_msg",
                "params": {"user_id": receive["user_id"], "message": msg},
            }
        )
    return action


def group_ban_action(group_id, user_id, duration):
    action = {
        "action": "set_group_ban",
        "params": {"group_id": group_id, "user_id": user_id, "duration": duration},
        "echo": "",
    }
    return action


def delete_message_action(message_id):
    action = {"action": "delete_msg", "params": {"message_id": message_id}, "echo": ""}
    return action


# Weibo share
def get_weibotile_share(weibotile, mode="json"):
    content_json = json.loads(weibotile.content)
    mblog = content_json["mblog"]
    bs = BeautifulSoup(mblog["text"], "lxml")
    tmp = {
        "url": content_json["scheme"],
        "title": bs.get_text().replace("\u200b", "")[:32],
        "content": "From {}'s Weibo".format(weibotile.owner),
        "image": mblog["user"]["profile_image_url"],
    }
    res_data = tmp
    if mode == "text":
        res_data = "[[CQ:share,url={},title={},content={},image={}]]".format(
            tmp["url"], tmp["title"], tmp["content"], tmp["image"]
        )
    logging.debug("weibo_share")
    logging.debug(json.dumps(res_data))
    return res_data


# Weather
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

    step1 = ((calcBase << 11) % (0x100000000)) ^ calcBase
    step2 = ((step1 >> 8) % (0x100000000)) ^ step1

    return step2 % 100


def getEorzeaHour(unixSeconds):
    bell = (unixSeconds / 175) % 24
    return int(bell)


def getEorzeaDay(unixSeconds):
    Day = unixSeconds / 175 / 24 % 32
    return int(Day)


def getEorzeaMonth(unixSeconds):
    Month = unixSeconds / 175 / 24 / 32 % 12
    return int(Month)


def getEorzeaYear(unixSeconds):
    Year = unixSeconds / 175 / 24 / 32 / 12
    return int(Year)


def getWeatherTimeFloor(unixSeconds):
    # Get Eorzea hour for weather start
    bell = (unixSeconds / 175) % 24
    startBell = bell - (bell % 8)
    startUnixSeconds = round(unixSeconds - (175 * (bell - startBell)))
    return startUnixSeconds


def getGarlokWeatherTimeFloor(unixSeconds):
    bell = (unixSeconds / 175) % 24
    startBell = bell - (bell % 8)
    startUnixSeconds = round(unixSeconds - (175 * (bell - startBell)) - (9 * 8 * 175))
    return startUnixSeconds


def getWeatherID(territory, chance):
    weather_rate = json.loads(territory.weather_rate.rate)
    lrate = 0
    for (weather_id, rate) in weather_rate:
        if lrate <= chance < lrate + rate:
            return weather_id
        lrate += rate

    print("can't find {} chance:{}".format(territory, chance))
    return -1


def getFollowingWeathers(territory, cnt=5, TIMEFORMAT="%m-%d %H:%M:%S", **kwargs):
    Garlok = kwargs.get("Garlok", None)
    unixSeconds = kwargs.get("unixSeconds", int(time.time()))
    if Garlok:
        weatherStartTime = getGarlokWeatherTimeFloor(unixSeconds)
    else:
        weatherStartTime = getWeatherTimeFloor(unixSeconds)
    now_time = weatherStartTime
    weathers = []
    weather_rate = json.loads(territory.weather_rate.rate)
    for i in range(cnt):
        chance = calculateForecastTarget(now_time)
        weather_id = getWeatherID(territory, chance)
        pre_chance = calculateForecastTarget(now_time - 8 * 175)
        pre_weather_id = getWeatherID(territory, pre_chance)
        # print("weather_id:{}".format(weather_id))
        try:
            weather = Weather.objects.get(id=weather_id)
        except Weather.DoesNotExist as e:
            raise e
        try:
            pre_weather = Weather.objects.get(id=pre_weather_id)
        except Weather.DoesNotExist as e:
            raise e

        weathers.append(
            {
                "pre_name": "{}".format(pre_weather),
                "name": "{}".format(weather),
                "ET": "{}:00".format(getEorzeaHour(now_time)),
                "LT": "{}".format(time.strftime(TIMEFORMAT, time.localtime(now_time))),
            }
        )
        now_time += 8 * 175
    return weathers


def getSpecificWeatherTimes(
    territory, weathers, cnt=5, TIMEFORMAT_MDHMS="%m-%d %H:%M:%S"
):
    unixSeconds = int(time.time())
    weatherStartTime = getWeatherTimeFloor(unixSeconds)
    count = cnt
    match = 0
    times = []
    weather_rate = json.loads(territory.weather_rate.rate)
    now_time = weatherStartTime
    try_time = 0
    while match < abs(count) and try_time <= 1000:
        try_time += 1
        chance = calculateForecastTarget(now_time)
        weather_id = getWeatherID(territory, chance)
        pre_chance = calculateForecastTarget(now_time - 8 * 175)
        pre_weather_id = getWeatherID(territory, pre_chance)
        try:
            pre_weather = Weather.objects.get(id=pre_weather_id)
        except Weather.DoesNotExist as e:
            raise e
        for weather in weathers:
            if weather_id == weather.id:
                times.append(
                    {
                        "pre_name": "{}".format(pre_weather),
                        "name": "{}".format(weather),
                        "ET": "{}:00".format(getEorzeaHour(now_time)),
                        "LT": "{}".format(
                            time.strftime(TIMEFORMAT_MDHMS, time.localtime(now_time))
                        ),
                    }
                )
                match += 1
                break
        now_time += 8 * 175
    return times


def crawl_dps(boss, job, day=0, CN_source=False, dps_type="adps"):
    print("boss:{} job:{} day:{}".format(boss, job, day))
    fflogs_url = "https://www.fflogs.com/zone/statistics/table/{}/dps/{}/{}/8/{}/100/1000/7/{}/Global/{}/All/0/normalized/single/0/-1/?keystone=15&dpstype={}".format(
        boss.quest.quest_id,
        boss.boss_id,
        boss.savage,
        boss.cn_server if CN_source else boss.global_server,
        boss.patch,
        job.name,
        dps_type,
    )
    print("fflogs url:{}".format(fflogs_url))
    s = requests.Session()
    s.headers.update({"referer": "https://www.fflogs.com"})
    r = s.get(url=fflogs_url, timeout=5)
    tot_days = 0
    percentage_list = [10, 25, 50, 75, 95, 99, 100]
    atk_res = {}
    for perc in percentage_list:
        if perc == 100:
            re_str = "series" + r".data.push\([+-]?(0|([1-9]\d*))(\.\d+)?\)"
        else:
            re_str = "series%s" % (perc) + r".data.push\([+-]?(0|([1-9]\d*))(\.\d+)?\)"
        ptn = re.compile(re_str)
        find_res = ptn.findall(r.text)
        if CN_source and boss.cn_offset:
            find_res = find_res[boss.cn_offset :]
        # print("found {} atk_res".format(len(find_res)))
        try:
            if day == -1:
                day = len(find_res) - 1
            atk_res[str(perc)] = find_res[day]
        except IndexError as e:
            day = len(find_res)
            if day:
                atk_res[str(perc)] = find_res[-1]
            else:
                return "No data found"
        ss = atk_res[str(perc)][1] + atk_res[str(perc)][2]
        if ss == "":
            ss = "0"
        atk = float(ss)
        atk_res[str(perc)] = atk
        atk_res["day"] = day
    return atk_res


def get_item_info(data, lang="", item_url=""):
    api_base = CAFEMAKER if lang == "cn" else XIVAPI
    url = api_base + data["Url"]
    if lang == "cn":
        lang = "chs"
    try:
        r = requests.get(url, timeout=5)
        j = r.json()
        name = j["Name_{}".format(lang)] if lang else j["Name"]
        desc = j["Description_{}".format(lang)] if lang else j["Description"]
        if not desc:
            desc = name
        if r.status_code == 200:
            res_data = {
                "url": item_url,
                "title": name,
                "content": desc,
                "image": api_base + j["Icon"],
            }
        else:
            res_data = {
                "url": url,
                "title": "FF14 API 炸了",
                "content": "HTTP {}".format(r.status_code),
                "image": "",
            }
    except requests.exceptions.ReadTimeout:
        res_data = {
            "url": url,
            "title": "%s 的道具查询请求超时了" % (data["Name"]),
            "content": "不信你自己打开看看",
            "image": "",
        }
    return res_data


def get_xivapi_item(item_name, name_lang=""):
    api_base = CAFEMAKER if name_lang == "cn" else XIVAPI
    url = api_base + "/search?indexes=Item&string=" + item_name
    if name_lang:
        url = url + "&language=" + name_lang
    r = requests.get(url, timeout=3)
    j = r.json()
    return j, url


def search_item(name, FF14WIKI_BASE_URL, FF14WIKI_API_URL, url_quote=True):
    try:
        found = False
        for lang in ["cn", "en", "ja", "fr", "de"]:
            j, search_url = get_xivapi_item(name, lang)
            if j.get("Results"):
                found = True
                name_lang = lang
                break
        if not found:
            return False
        api_base = CAFEMAKER if name_lang == "cn" else XIVAPI
        res_num = j["Pagination"]["ResultsTotal"]
        if res_num == 1:
            item_name = j["Results"][0]["Name"]
            item_url = (
                FF14WIKI_BASE_URL
                + "/wiki/"
                + urllib.parse.quote("物品")
                + ":"
                + urllib.parse.quote(item_name)
            )
            if name_lang == "en":
                item_url = "http://www.garlandtools.org/db/#item/{}".format(
                    j["Results"][0]["ID"]
                )
            elif name_lang == "ja":
                item_url = "https://eriones.com/search?i=%E3%82%AB%E3%83%96%E3%82%B9%E3%81%AE%E8%82%89"
            logging.debug("/search %s %s" % (item_name, item_url))
            res_data = get_item_info(j.get("Results")[0], name_lang, item_url)
        else:
            search_url = (
                FF14WIKI_BASE_URL + "/wiki/ItemSearch?name=" + urllib.parse.quote(name)
            )
            res_data = {
                "url": search_url,
                "title": "%s 的搜索结果" % (name),
                "content": "在最终幻想XIV中找到了 %s 个物品" % (res_num),
                "image": api_base + j["Results"][0]["Icon"],
            }
        logging.debug("res_data:%s" % (res_data))
    except requests.exceptions.ReadTimeout:
        res_data = {
            "url": search_url,
            "title": "%s 的搜索请求超时了" % (name),
            "content": "不信你自己打开看看",
            "image": "",
        }
    except json.decoder.JSONDecodeError:
        print(r.text)

    print(res_data)
    return res_data


def check_raid(api_url, raid_data, raid_name, wol_name, server_name):
    data = raid_data
    try:
        r = requests.post(url=api_url, data=data, timeout=5)
        res = json.loads(r.text)
        msg = ""
        if int(res["Code"]) != 0:
            msg += res["Message"]
        else:
            ok = False
            raid_info = ""
            for i in range(4):
                l = i + 1
                level = "Level{}".format(l)
                if res["Attach"][level]:
                    ok = True
                    if len(res["Attach"][level].strip()) == 8:
                        date = res["Attach"][level]
                        fdate = "{}-{}-{}".format(date[:4], date[4:6], date[6:8])
                        raid_info += "{}{}: {}\n".format(raid_name, l, fdate)
                    else:
                        raid_info += "{}{}: 数据缺失\n".format(raid_name, l)
                else:
                    raid_info += "{}{}: 仍未攻破\n".format(raid_name, l)
            if not ok:
                msg += "{}--{} 还没有突破过任何零式{}，请继续努力哦~\n".format(
                    server_name, wol_name, raid_name
                )
            else:
                msg = (
                    "{}--{} 的 {} 挑战情况如下：\n".format(server_name, wol_name, raid_name)
                    + raid_info
                )
    except requests.exceptions.ReadTimeout:
        msg = "raid请求超时，请检查后台日志"
    return msg


def text2img(text):
    font = ImageFont.truetype(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resources/font/msyh.ttc",
        ),
        20,
    )
    lines = text.split("\n")
    img_height = 0
    img_width = 0
    for line in lines:
        width, height = font.getsize(line)
        img_width = max(img_width, width)
        img_height += height
    border = 10
    img = PILImage.new(
        "RGB", (img_width + 2 * border, img_height + 2 * border), color="white"
    )
    d = ImageDraw.Draw(img)
    d.text((border, border), text, font=font, fill="#000000")
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="JPEG")
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode("utf-8")
    msg = "[CQ:image,file=base64://{}]\n".format(base64_str)
    return msg

class TagCompletion(object):
    # 补全konachan搜图的tag
    def __init__(self, vocab):
        self.force = False
        self.TAGS = json.load(open(vocab, "r", encoding="utf-8"))

    def freq(self, word):
        return self.TAGS.get(word, 0)

    def select_tag(self, input_tag_name):
        if self.TAGS.get(input_tag_name, None) is not None:
            real_tag = input_tag_name
        else:
            close_matches = difflib.get_close_matches(
                input_tag_name, self.TAGS.keys()
            )
            if close_matches:
                # print("select by close match")
                real_tag = close_matches[0]
            else:
                if not self.force:
                    real_tag = input_tag_name
                else:
                    # 强制返回一个合法（有搜索结果）的随机tag
                    real_tag = random.choice(list(self.TAGS.keys()))
        return real_tag

def update_konachan_tags():
    # 截至2020.10.19 konachan拥有近8万个各种种类的tag
    url = "https://konachan.net/tag.json?limit=999999"
    all_tags = requests.get(url, timeout=(5, 60)).json()
    reserved_tags = {
        tag["name"]: tag["count"]
        for tag in filter(lambda tag: not tag["ambiguous"] and tag["count"] and re.match(r"^.*[a-z0-9\u4e00-\u9fa5].*$", tag["name"], re.I), all_tags)
    }
    json.dump(reserved_tags, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "konachan_tags.json"), 'w', encoding='utf-8'))
