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
import redis
from bs4 import BeautifulSoup
from PIL import ImageFont, ImageDraw
from PIL import Image as PILImage

from ffxivbot.models import *

# garlandtools.cn locates in China
# ffxiv.cyanclay.xyz locates in German, boosted by cloudflare
# choose your better server here!
GARLAND = "https://ffxiv.cyanclay.xyz"

CAFEMAKER = "https://cafemaker.wakingsands.com"
XIVAPI = "https://xivapi.com"

XIV_TAG_REGEX = re.compile(r"<(.*?)>")
GT_CORE_DATA_CN = None
GT_CORE_DATA_GLOBAL = None
NODE_NAME_BY_TYPE = {
    0: "矿脉",
    1: "石场",
    2: "良材",
    3: "草场",
    4: "鱼影",
    5: "鱼影"
}

FISH_SHADOW_SIZE = {
    'S': '小型',
    'M': '中型',
    'L': '大型',
    'Map': '宝藏地图'
}

FISH_SHADOW_SPEED = {
    'Slow': '慢',
    'Average': '中速',
    'Fast': '快',
    'Very Fast': '非常快',
    'V. Fast': '非常快'
}


def get_CQ_image(CQ_text):
    image_pattern = r"\[CQ:(?:image),.*(?:url|file)=(https?://.*)\]"
    match = re.findall(image_pattern, CQ_text)
    return match[0] if match else None


def reply_message_action(receive, msg):
    action = {"action": "", "params": {}, "echo": ""}
    if type(msg) == list:
        msg.append({
            "type": "reply",
            "data": {"id": receive["message_id"]}
        })
    else:
        msg += f"[CQ:reply,id={receive['message_id']}]"
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
    redis_client = redis.Redis(host="localhost", port=6379, decode_responses=True)
    hash_key = "fflogs|{}".format(fflogs_url)
    cached_stat_list = redis_client.get(hash_key)
    if not cached_stat_list:
        s = requests.Session()
        s.headers.update({"referer": "https://www.fflogs.com"})
        r = s.get(url=fflogs_url, timeout=5)
        percentage_list = [10, 25, 50, 75, 95, 99, 100]
        statistics = {}
        for percentage in percentage_list:
            re_str = "series{}".format(
                "" if percentage == 100 else percentage) + r".data.push\([+-]?(0|(?:[1-9]\d*)(?:\.\d+)?)\)"
            ptn = re.compile(re_str)
            find_res = ptn.findall(r.text)
            statistics[str(percentage)] = list(map(lambda x: float(x), find_res))
        total_length = len(statistics['100'])
        for percentage in percentage_list:
            assert len(statistics[str(percentage)]) == total_length, "Length of parsed dps aren't consistent"
        l = 0
        r = total_length - 1

        def all_0(stat, idx):
            sum_dps = 0
            for perc in percentage_list:
                sum_dps += stat[str(perc)][idx]
            return sum_dps == 0

        while l < total_length and all_0(statistics, l):
            l += 1
        while r >= 0 and all_0(statistics, r):
            r -= 1
        if l > r or l >= total_length or r < 0:
            return "No data found"
        stat_list = []
        for idx, (p10, p25, p50, p75, p95, p99, p100) in enumerate(zip(
                statistics['10'][l:r + 1],
                statistics['25'][l:r + 1],
                statistics['50'][l:r + 1],
                statistics['75'][l:r + 1],
                statistics['95'][l:r + 1],
                statistics['99'][l:r + 1],
                statistics['100'][l:r + 1],
        ), 1):
            stat_list.append({
                'day': idx,
                '10': p10,
                '25': p25,
                '50': p50,
                '75': p75,
                '95': p95,
                '99': p99,
                '100': p100,
            })
        redis_client.set(
            hash_key,
            json.dumps(stat_list),
            ex=3600,
        )
    else:
        stat_list = json.loads(cached_stat_list)

    if not stat_list:
        return "No data found"

    if day == -1 or day >= len(stat_list):
        return stat_list[-1]

    return stat_list[day]


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


def craft_wiki_url(item_name=""):
    return "https://ff14.huijiwiki.com" + "/wiki/" \
           + urllib.parse.quote("物品") + ":" + urllib.parse.quote(item_name)


# use garlandtools.cn if your server is in China
# else use ffxiv.cyanclay.xyz, which located at German
def craft_garland_url(item_category, item_id, name_lang):
    is_cn = (name_lang == "chs")
    return "{}/db/doc/{}/{}/3/{}.json".format(
        GARLAND if is_cn else "https://garlandtools.org",
        item_category,
        name_lang,
        item_id
    )


def parse_xiv_html(string):
    global XIV_TAG_REGEX

    def handle_tag(tag_match):
        tag = tag_match.group(1)
        return '\n' if tag == "br" else ""

    return XIV_TAG_REGEX.sub(handle_tag, string)


def gt_core(key: str, lang: str):
    global GT_CORE_DATA_CN, GT_CORE_DATA_GLOBAL
    if lang == "chs":
        if GT_CORE_DATA_CN is None:
            GT_CORE_DATA_CN = requests.get(craft_garland_url("core", "data", "chs"), timeout=3).json()
        GT_CORE_DATA = GT_CORE_DATA_CN
    else:
        if GT_CORE_DATA_GLOBAL is None:
            GT_CORE_DATA_GLOBAL = requests.get(craft_garland_url("core", "data", "en"), timeout=3).json()
        GT_CORE_DATA = GT_CORE_DATA_GLOBAL
    req = GT_CORE_DATA
    for par in key.split('.'):
        req = req[par]
    return req


def parse_item_garland(item_id, name_lang):
    if name_lang == "cn":
        name_lang = "chs"

    j = requests.get(craft_garland_url("item", item_id, name_lang), timeout=3).json()

    result = []
    # index partials
    partials = {}
    for p in j["partials"] if "partials" in j.keys() else []:
        partials[(p["type"], p["id"])] = p["obj"]

    item = j["item"]
    # start processing
    if "icon" in item.keys():
        image_url = f"{GARLAND}/files/icons/item/{item['icon'] if str(item['icon']).startswith('t/') else 't/' + str(item['icon'])}.png"
        image = requests.get(image_url)
        base64_str = base64.b64encode(image.content).decode("utf-8")
        result.append(f"[CQ:image,file=base64://{base64_str}]")

    result.append(item["name"])
    result.append(gt_core(f"item.categoryIndex.{item['category']}.name", name_lang))
    result.append(f"物品等级 {item['ilvl']}")
    if "equip" in item.keys():
        result.append(f"装备等级 {item['elvl']}")

    if "jobCategories" in item.keys():
        result.append(item['jobCategories'])

    if "description" in item.keys():
        result.append(parse_xiv_html(item['description']))

    hasSource = False

    def format_limit_time(times):
        limitTimes = "\n艾欧泽亚时间 "
        for time in times:
            limitTimes += f"{time}时 "
        limitTimes += "开放采集"
        return limitTimes

    if "nodes" in item.keys():
        global NODE_NAME_BY_TYPE
        hasSource = True
        result.append(f"·采集")
        for nodeIndex in item["nodes"]:
            node = partials[("node", str(nodeIndex))]
            result.append("  -- {} {} {} {}{}".format(
                gt_core(f"locationIndex.{node['z']}.name", name_lang),
                node["n"],
                "{}{}".format(
                    "" if 'lt' not in node.keys() else node['lt'],
                    NODE_NAME_BY_TYPE[int(node['t'])]
                ),
                f"({node['c'][0]}, {node['c'][1]})",
                "" if 'ti' not in node.keys() else format_limit_time(node['ti'])
            ))
        result.append("")

    if "fishingSpots" in item.keys():
        hasSource = True
        result.append(f"·钓鱼")
        for spotIndex in item['fishingSpots']:
            spot = partials[("fishing", str(spotIndex))]
            result.append("  -- {} {} {} {}".format(
                gt_core(f"locationIndex.{spot['z']}.name", name_lang),
                spot['n'],
                f"{spot['c']} {spot['l']}级",
                "" if 'x' not in spot.keys() else f"({spot['x']}, {spot['y']})"
            ))
        result.append("")

    if "fish" in item.keys():
        result.append(f"·钓法/刺鱼指引")
        for fishGroup in item['fish']['spots']:
            if "spot" in fishGroup.keys():
                result.append(f"  {fishGroup['hookset']} {fishGroup['tug']}")
                if "predator" in fishGroup.keys():
                    result.append("- 需求捕鱼人之识")
                    for predator in fishGroup['predator']:
                        result.append("  - {} *{}".format(
                            partials[("item", str(predator["id"]))]['n'],
                            predator['amount']
                        ))
                if "baits" in fishGroup.keys():
                    result.append("- 可用鱼饵")
                    for baitChains in fishGroup['baits']:
                        chain = ""
                        for bait in baitChains:
                            if not len(chain) == 0:
                                chain += " -> "
                            chain += partials[('item', str(bait))]['n']
                        result.append(f"  - {chain}")
                if "during" in fishGroup.keys():
                    result.append(f"- 限ET {fishGroup['during']['start']}时至{fishGroup['during']['end']}时")
                if "weather" in fishGroup.keys():
                    w = " ".join(fishGroup['weather'])
                    if "transition" in fishGroup.keys():
                        w = w + " -> " + " ".join(fishGroup['transition'])
                    result.append(f"- 限{w}")
            elif "node" in fishGroup.keys():
                result.append(f"- 鱼影大小 {FISH_SHADOW_SIZE[fishGroup['shadow']]}")
                result.append(f"- 鱼影速度 {FISH_SHADOW_SPEED[fishGroup['speed']]}")
                pass
        result.append("")

    if "reducedFrom" in item.keys():
        hasSource = True
        result.append(f"·精选")
        for itemIndex in item["reducedFrom"]:
            result.append("- {}".format(partials[("item", str(itemIndex))]['n']))
        result.append("")

    if "craft" in item.keys():
        hasSource = True
        result.append(f"·制作")
        for craft in item["craft"]:
            result.append("  -- {} {}".format(
                gt_core(f"jobs", name_lang)[craft["job"]]["name"],
                f"{craft['lvl']}级"
            ))
            result.append("  材料:")
            for ingredient in craft["ingredients"]:
                if ingredient["id"] < 20:
                    continue
                result.append("   - {} {}个".format(
                    partials[("item", str(ingredient["id"]))]["n"],
                    ingredient["amount"]
                ))
        result.append("")

    if "vendors" in item.keys():
        hasSource = True
        result.append(f"·商店贩售 {item['price']}金币")
        i = 0
        for vendor in item["vendors"]:
            if i > 4:
                result.append(f"等共计{len(item['vendors'])}个商人售卖")
                break
            vendor_partial = partials["npc", str(vendor)]
            result.append("  -- {} {} {}".format(
                vendor_partial["n"],
                gt_core(f"locationIndex.{vendor_partial['l']}.name", name_lang) if 'l' in vendor_partial.keys() else "",
                f"({vendor_partial['c'][0]}, {vendor_partial['c'][1]})" if 'c' in vendor_partial.keys() else ""
            ))
            i += 1
        pass

    if "tradeCurrency" in item.keys() or "tradeShops" in item.keys():
        hasSource = True
        tradeCurrency = []
        tradeShops = []
        try:
            tradeCurrency = item["tradeCurrency"]
        except KeyError:
            # ignore
            pass
        try:
            tradeShops = item["tradeShops"]
        except KeyError:
            # ignore
            pass
        trades = tradeCurrency + tradeShops
        i = 0
        for trade in trades:
            if i > 4:
                result.append(f"等共计{len(trades)}种购买方式")
                break

            shop_name = trade["shop"]
            result.append("·{}".format(
                "商店交易" if shop_name == "Shop" else shop_name,
            ))

            j = 0
            for vendor in trade["npcs"]:
                if j > 2:
                    result.append(f"等共计{len(trade['npcs'])}个商人交易")
                    break
                vendor_partial = partials["npc", str(vendor)]
                result.append("  -- {} {} {}".format(
                    vendor_partial["n"],
                    gt_core(f"locationIndex.{vendor_partial['l']}.name", name_lang) if 'l' in vendor_partial.keys() else "",
                    f"({vendor_partial['c'][0]}, {vendor_partial['c'][1]})" if 'c' in vendor_partial.keys() else ""
                ))
                j += 1
            j = 0
            for listing in trade["listings"]:
                if j > 2:
                    result.append(f"等共计{len(trade['listings'])}种兑换方式")
                    break
                listing_str = ""
                currency_str = ""
                k = 0
                for listingItem in listing["item"]:
                    if k > 2:
                        result.append(f"等共计{len(listing['item'])}项商品兑换")
                        break
                    listing_str += "- {}{} *{}\n".format(
                        item["name"] if str(listingItem["id"]) == str(item_id) else
                        partials[("item", str(listingItem["id"]))]['n'],
                        'HQ' if 'hq' in listingItem.keys() else '',
                        listingItem['amount']
                    )
                    k += 1
                k = 0
                for currency in listing["currency"]:
                    if k > 2:
                        result.append(f"等共计{len(listing['currency'])}项商品兑换")
                        break
                    currency_str += "- {}{} *{}\n".format(
                        item["name"] if str(currency["id"]) == str(item_id) else
                        partials[("item", str(currency["id"]))]['n'],
                        'HQ' if 'hq' in currency.keys() else '',
                        currency['amount']
                    )
                result.append("使用\n{}兑换获得\n{}".format(currency_str, listing_str))

    if "drops" in item.keys():
        hasSource = True
        result.append(f"·怪物掉落")
        for mobIndex in item["drops"]:
            mob = partials[("mob", str(mobIndex))]
            result.append("  -- {} {}".format(
                mob['n'],
                gt_core(f"locationIndex.{mob['z']}.name", name_lang)
            ))
        result.append("")

    if "instances" in item.keys():
        hasSource = True
        result.append(f"·副本获取")
        i = 0
        for dutyIndex in item["instances"]:
            if i > 4:
                result.append(f"等共计{len(item['instances'])}个副本获取")
                break
            duty = partials[("instance", str(dutyIndex))]
            result.append("  -- {}级 {}".format(
                duty['min_lvl'], duty['n']
            ))
            i += 1
        result.append("")

    if "quests" in item.keys():
        hasSource = True
        result.append(f"·任务奖励")
        i = 0
        for questIndex in item["quests"]:
            if i > 4:
                result.append(f"等共计{len(item['instance'])}个任务奖励")
                break
            quest = partials[("quest", str(questIndex))]
            result.append("  -- {}\n{}".format(
                quest["n"], f"https://garlandtools.cn/db/#quest/{quest['i']}"
            ))
            i += 1
        result.append("")

    if not hasSource:
        result.append("获取方式较麻烦/没查到，烦请打开网页查看！")

    status = ""

    if "unique" in item.keys():
        status += f"独占 "

    if "tradeable" in item.keys():
        status += f"{'' if bool(item['tradeable']) else '不'}可交易 "

    if "unlistable" in item.keys():
        status += f"{'不' if bool(item['unlistable']) else ''}可在市场上交易 "

    if "reducible" in item.keys():
        status += f"{'' if bool(item['reducible']) else '不'}可精选 "

    if "storable" in item.keys():
        status += f"{'' if bool(item['storable']) else '不'}可放入收藏柜 "

    if not status.isspace():
        result.append(status)

    result.append(f"https://garlandtools.{'cn' if name_lang == 'chs' else 'org'}/db/#item/{item_id}")

    return "\n".join(result)


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
        name_lang = None
        for lang in ["cn", "en", "ja", "fr", "de"]:
            j, search_url = get_xivapi_item(name, lang)
            if j.get("Results"):
                name_lang = lang
                break
        if name_lang is None:
            return False
        api_base = CAFEMAKER if name_lang == "cn" else XIVAPI
        res_num = j["Pagination"]["ResultsTotal"]

        if res_num == 1 or j["Results"][0]["Name"] == name:
            try:
                return parse_item_garland(j["Results"][0]["ID"], name_lang)
            except Exception as e:
                return f"搜索失败！{repr(e)}"
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
        print(j.text)

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
    text = text.strip()
    # print("=====\n{}\n=====".format(text))
    font = ImageFont.truetype(
        os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "resources/font/msyh.ttc",
        ),
        20,
    )
    lines = text.split("\n")
    # while "" in lines:
    #     lines.remove("")
    # text = "\n".join(lines)
    img_height = 0
    last_height = 0
    img_width = 0
    border = 10
    _, height = font.getsize(text)
    for line in lines:
        # print("{}:\t{}".format(img_height + border, line))
        width, _ = font.getsize(line)
        img_width = max(img_width, width)
        img_height += height
    img = PILImage.new(
        "RGB", (img_width + 2 * border, img_height + 2 * border), color="white"
    )

    # print((img_width + 2 * border, img_height + 2 * border))
    d = ImageDraw.Draw(img)
    d.text((border, border), text, font=font, fill="#000000")
    output_buffer = io.BytesIO()
    img.save(output_buffer, format="JPEG")
    byte_data = output_buffer.getvalue()
    base64_str = base64.b64encode(byte_data).decode("utf-8")
    msg = "[CQ:image,file=base64://{}]\n".format(base64_str)
    # print("=====\nbase64://{}\n=====".format(base64_str))
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
        for tag in filter(
            lambda tag: not tag["ambiguous"]
                        and tag["count"]
                        and re.match(r"^.*[a-z0-9\u4e00-\u9fa5].*$", tag["name"], re.I),
            all_tags)
    }
    json.dump(reserved_tags,
              open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "konachan_tags.json"), 'w',
                   encoding='utf-8'))
