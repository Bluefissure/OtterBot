import json
import re
import requests
import urllib.parse
import os
import logging
from dotenv import load_dotenv

load_dotenv()

API_BASE = os.environ.get('API_BASE', '')
RED_BASE = os.environ.get('RED_BASE', '')  # TODO

_log = logging.getLogger("QQBot Guilds")

def handle_quest(quest_name):
    post_data = {
        "request": "quest",
        "data": {
            "name": quest_name
        }
    }
    r = requests.post(API_BASE, json=post_data)
    ret_data = r.json()
    _log.debug(json.dumps(ret_data, indent=2))
    if int(ret_data["rcode"]) != 0:
        return { "message": "在最终幻想XIV中没有找到任务\"{}\"".format(quest_name) }
    ret_data = ret_data["data"]["data"]
    image = ret_data.get('banner', ret_data.get('image', ''))
    image_url = (RED_BASE + urllib.parse.quote(image)) if image else ''
    msg = "{}\n{}".format(ret_data["title"], ret_data["content"])
    result = { "message": msg }
    if image:
        result['image'] = image_url
    return result


def handle_search(item_name):
    post_data = {
        "request": "search",
        "data": {
            "name": item_name
        }
    }
    r = requests.post(API_BASE, json=post_data)
    try:
        ret_data = r.json()
    except requests.exceptions.JSONDecodeError:
        return { "message": "解析失败，请联系开发者排查" }
    _log.debug(json.dumps(ret_data, indent=2))
    if type(ret_data["data"]) == bool:
        return { "message": "在最终幻想XIV中没有找到道具\"{}\"".format(item_name) }
    if type(ret_data["data"]) == str:
        ret_msg = re.sub(r"\[CQ:image,file=.*?\]", "", ret_data["data"])
        # ret_msg = re.sub(r"https://garlandtools.cn/db/#item/\d+", "", ret_msg)
        return { "message": ret_msg.strip() }
    ret_data = ret_data["data"]
    msg = "{}\n{}".format(ret_data["title"], ret_data["content"])
    return {
        "message": msg,
    }

def handle_market(command_seg):
    help_msg = """/market item $name $server: 查询$server服务器的$name物品交易数据
/market upload: 如何上报数据
Powered by universalis"""
    msg = help_msg
    if len(command_seg) == 0 or command_seg[0].lower() == "help":
        return { "message": msg }
    elif command_seg[0].lower() == "item" or len(command_seg) == 2:
        if len(command_seg) == 2:
            command_seg = ["item"] + command_seg
        if len(command_seg) != 3:
            msg = "参数错误：\n/market item $name $server: 查询$server服务器的$name物品交易数据"
            return { "message": msg }
        server_name = command_seg[-1]
        item_name = " ".join(command_seg[1:-1])
        hq = "hq" in item_name or "HQ" in item_name
        if hq:
            item_name = item_name.replace("hq", "", 1)
            item_name = item_name.replace("HQ", "", 1)
        post_data = {
            "request": "market",
            "data": {
                "item_name": item_name,
                "server_name": server_name,
                "hq": hq
            }
        }
        r = requests.post(API_BASE, json=post_data)
        ret_data = r.json()
        _log.debug(json.dumps(ret_data, indent=2))
        if ret_data['rcode'] == '0':
            msg = ret_data['data']
        else:
            msg = 'API error, please check log.'
        return { "message": msg }
    elif command_seg[0].lower() == "upload":
        msg = """您可以使用以下几种方式上传交易数据：
0.如果您使用咖啡整合的ACT，可以启用抹茶插件中的Universalis集成功能
1.如果您使用过国际服的 XIVLauncher，您可以使用国服支持的Dalamud版本
2.如果您使用过ACT，您可以加载ACT插件 UniversalisPlugin
3.如果您想不依赖于其他程序，您可以使用 UniversalisStandalone
4.如果您使用过Teamcraft客户端，您也可以使用其进行上传"""
    return { "message": msg }


def handle_luck(command_seg, user_id):
    help_msg = """使用命令 /luck 获得今日艾欧泽亚运势
对结果不满意，可以使用\"/luck r\"来重抽
重构自：onebot_Astrologian_FFXIV"""
    msg = help_msg
    if len(command_seg) > 1 and command_seg[0].lower() == "help":
        return { "message": msg }
    else:
        if len(command_seg) == 0:
            redraw = False
        else:
            redraw = command_seg[0].lower() in ("r", "redraw")
        post_data = {
            "request": "luck",
            "data": {
                "user_id": user_id,
                "redraw": redraw,
            }
        }
        r = requests.post(API_BASE, json=post_data)
        ret_data = r.json()
        _log.debug(json.dumps(ret_data, indent=2))
        if ret_data['rcode'] == '0':
            msg = ret_data['data']
        else:
            msg = 'API error, please check log.'
    return { "message": msg }

def on_at_message_create(message, qqbot):
    _log.info(json.dumps(message, indent=2, ensure_ascii=False))
    data = message['d']
    channel_id = data['channel_id']
    user_id = data['author']['id']
    content = re.sub(r"<@!.*>", "", data['content']).strip()
    msg = None
    image = None
    if content.startswith("/ping"):
        qqbot.log.info(f"Get pinged from channel:{channel_id}")
        qqbot.reply_channel_message(message, content=f"Pong! ({channel_id})")
        return
    if content.startswith("/quest"):
        quest_name = content.replace("/quest", "").strip()
        msg_object = handle_quest(quest_name)
        if "ark" in msg_object:
            ark = msg_object["ark"]
        else:
            msg = msg_object["message"]
            # image = msg_object.get('image')
    if content.startswith("/search"):
        item_name = content.replace("/search", "").strip()
        msg_object = handle_search(item_name)
        if "ark" in msg_object:
            ark = msg_object["ark"]
        else:
            msg = msg_object["message"]
    if content.startswith("/market") or content.startswith("/mitem"):
        args_str = content.replace("/mitem", "/market item").replace("/market", "").strip()
        args = args_str.split(" ")
        while '' in args:
            args.remove('')
        msg_object = handle_market(args)
        msg = msg_object["message"]
    if content.startswith("/luck"):
        args_str = content.replace("/luck", "").strip()
        args = args_str.split(" ")
        while '' in args:
            args.remove('')
        msg_object = handle_luck(args, user_id)
        msg = msg_object["message"]
    if msg:
        qqbot.log.info(msg)
        if image:
            qqbot.log.info("Sending image %s", image)
            qqbot.reply_channel_message(message, content=msg, image=image)
        else:
            qqbot.reply_channel_message(message, content=msg)