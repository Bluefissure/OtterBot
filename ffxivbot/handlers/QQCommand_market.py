from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
from difflib import SequenceMatcher
import logging
import json
import random
import dice
import feedparser
import traceback
import requests
import time
import re
from bs4 import BeautifulSoup


def localize_world_name(world_name):
    world_dict = {
        "HongYuHai": "红玉海",
        "ShenYiZhiDi": "神意之地",
        "LaNuoXiYa": "拉诺西亚",
        "HuanYingQunDao": "幻影群岛",
        "MengYaChi": "萌芽池",
        "YuZhouHeYin": "宇宙和音",
        "WoXianXiRan": "沃仙曦染",
        "ChenXiWangZuo": "晨曦王座",
        "BaiYinXiang": "白银乡",
        "BaiJinHuanXiang": "白金幻象",
        "ShenQuanHen": "神拳痕",
        "ChaoFengTing": "潮风亭",
        "LvRenZhanQiao": "旅人栈桥",
        "FuXiaoZhiJian": "拂晓之间",
        "Longchaoshendian": "龙巢神殿",
        "MengYuBaoJing": "梦羽宝境",
        "ZiShuiZhanQiao": "紫水栈桥",
        "YanXia": "延夏",
        "JingYuZhuangYuan": "静语庄园",
        "MoDuNa": "摩杜纳",
        "HaiMaoChaWu": "海猫茶屋",
        "RouFengHaiWan": "柔风海湾",
        "HuPoYuan": "琥珀原",
        "ShuiJingTa2": "水晶塔",
        "YinLeiHu2": "银泪湖",
        "TaiYangHaiAn2": "太阳海岸",
        "YiXiuJiaDe2": "伊修加德",
        "HongChaChuan2": "红茶川",
    }
    for (k, v) in world_dict.items():
        pattern = re.compile(k, re.IGNORECASE)
        world_name = pattern.sub(v, world_name)
    return world_name


def get_item_id(item_name, name_lang=""):
    url = "https://xivapi.com/search?indexes=Item&string=" + item_name
    if name_lang:
        url = url + "&language=" + name_lang
    if name_lang == "cn":
        url = (
            "https://cafemaker.wakingsands.com/search?indexes=Item&string=" + item_name
        )
    r = requests.get(url, timeout=60)
    j = r.json()
    if len(j["Results"]) > 0:
        result = max(j["Results"], key=lambda x: SequenceMatcher(None, x["Name"], item_name).ratio())
        return result["Name"], result["ID"]
    return "", -1


def get_market_data(server_name, item_name, hq=False):
    new_item_name, item_id = get_item_id(item_name, "cn")
    if item_id < 0:
        item_name = item_name.replace("_", " ")
        name_lang = ""
        for lang in ["ja", "fr", "de"]:
            if item_name.endswith("|{}".format(lang)):
                item_name = item_name.replace("|{}".format(lang), "")
                name_lang = lang
                break
        new_item_name, item_id = get_item_id(item_name, name_lang)
        if item_id < 0:
            return '所查询物品"{}"不存在'.format(item_name)
    url = "https://universalis.app/api/{}/{}".format(server_name, item_id)
    print("market url:{}".format(url))
    r = requests.get(url, timeout=10)
    if r.status_code != 200:
        if r.status_code == 404:
            msg = "请确认所查询物品可交易且不可在NPC处购买"
        else:
            msg = "Error of HTTP request (code {}):\n{}".format(r.status_code, r.text)
        return msg
    j = r.json()
    msg = "{} 的 {}{} 数据如下：\n".format(server_name, new_item_name, "(HQ)" if hq else "")
    listing_cnt = 0
    for listing in j["listings"]:
        if hq and not listing["hq"]:
            continue
        retainer_name = listing["retainerName"]
        if "dcName" in j:
            retainer_name += "({})".format(localize_world_name(listing["worldName"]))
        msg += "{:,}x{} = {:,} {} {}\n".format(
            listing["pricePerUnit"],
            listing["quantity"],
            listing["total"],
            "HQ" if listing["hq"] else "  ",
            retainer_name,
        )
        listing_cnt += 1
        if listing_cnt >= 10:
            break
    TIMEFORMAT_YMDHMS = "%Y-%m-%d %H:%M:%S"
    last_upload_time = time.strftime(
        TIMEFORMAT_YMDHMS, time.localtime(j["lastUploadTime"] / 1000)
    )
    msg += "更新时间:{}".format(last_upload_time)
    if listing_cnt == 0:
        msg = "未查询到数据，请使用/market upload命令查看如何上报数据"
    return msg


def handle_item_name_abbr(item_name):
    if item_name.startswith("第二期重建用的") and item_name.endswith("(检)"):
        item_name = item_name.replace("(", "（").replace(")", "）")
    if item_name.startswith("第二期重建用的") and not item_name.endswith("（检）"):
        item_name = item_name + "（检）"
    map_dict = {
        "G15": "陈旧的蛇牛革地图",
        "G14": "陈旧的金毗罗鳄革地图",
        "G13": "陈旧的赛加羚羊革地图",
        "G12": "陈旧的缠尾蛟革地图",
        "G11": "陈旧的绿飘龙革地图",
        "G10": "陈旧的瞪羚革地图",
        "G9": "陈旧的迦迦纳怪鸟革地图",
        "G8": "陈旧的巨龙革地图",
        "G7": "陈旧的飞龙革地图",
        "G6": "陈旧的古鸟革地图",
        "G5": "陈旧的毒蜥蜴革地图",
        "G4": "陈旧的野猪革地图",
        "G3": "陈旧的巨蟾蜍革地图",
        "G2": "陈旧的山羊革地图",
        "G1": "陈旧的鞣革地图",
        "绿图": "鞣革制的隐藏地图",
    }
    if item_name.upper() in map_dict:
        item_name = map_dict[item_name.upper()]
    return item_name


def handle_command(command_seg, user, group):
    help_msg = """/market item $name $server: 查询$server服务器的$name物品交易数据
/market upload: 如何上报数据
Powered by https://universalis.app"""
    msg = help_msg
    if len(command_seg) == 0 or command_seg[0].lower() == "help":
        return msg
    elif command_seg[0].lower() == "item":
        # if time.time() < user.last_api_time + user.api_interval:
        # print("current time:{}".format(time.time()))
        # print("last_api_time:{}".format(user.last_api_time))
        if time.time() < user.last_api_time + 15:
            msg = "[CQ:at,qq={}] 技能冷却中，请勿频繁调用".format(user.user_id)
            return msg
        server = None
        if len(command_seg) != 3:
            msg = "参数错误：\n/market item $name $server: 查询$server服务器的$name物品交易数据"
            return msg
        server_name = command_seg[-1]
        if server_name in ("陆行鸟", "莫古力", "猫小胖", "豆豆柴"):
            pass
        elif server_name == "鸟":
            server_name = "陆行鸟"
        elif server_name == "猪":
            server_name = "莫古力"
        elif server_name == "猫":
            server_name = "猫小胖"
        elif server_name == "狗":
            server_name = "豆豆柴"
        else:
            pass
            # server = Server.objects.filter(name=server_name)
            # if not server.exists():
            #     msg = '找不到服务器"{}"'.format(server_name)
            #     return msg
        item_name = " ".join(command_seg[1:-1])
        hq = "hq" in item_name or "HQ" in item_name
        if hq:
            item_name = item_name.replace("hq", "", 1)
            item_name = item_name.replace("HQ", "", 1)
        item_name = handle_item_name_abbr(item_name)
        msg = get_market_data(server_name, item_name, hq)
        user.last_api_time = time.time()
        user.save(update_fields=["last_api_time"])
        return msg
    elif command_seg[0].lower() == "upload":
        msg = """您可以使用以下几种方式上传交易数据：
0.如果您使用咖啡整合的ACT，可以启用抹茶插件中的Universalis集成功能 http://url.cn/a9xaUIKs 
1.如果您使用过国际服的 XIVLauncher，您可以使用国服支持的Dalamud版本 https://url.cn/6L7nD0gF
2.如果您使用过ACT，您可以加载ACT插件 UniversalisPlugin https://url.cn/TEY1QKKV
3.如果您想不依赖于其他程序，您可以使用 UniversalisStandalone https://url.cn/TEY1QKKV
4.如果您使用过Teamcraft客户端，您也可以使用其进行上传
Powered by https://universalis.app"""
    return msg


def QQCommand_market(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        # return [reply_message_action(receive, "Universalis 服务已宕机")]
        bot = kwargs["bot"]
        user = QQUser.objects.get(user_id=receive["user_id"])
        group = kwargs.get("group")
        msg = ""
        command_msg = receive["message"].replace("/market", "", 1).strip()
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
