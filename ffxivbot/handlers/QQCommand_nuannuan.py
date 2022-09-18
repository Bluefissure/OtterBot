from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import requests
import re
import traceback

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36"
}


def get_video_id(mid):
    try:
        # 获取用户信息最新视频的前五个，避免第一个视频不是攻略ps=5处修改
        url = f"https://api.bilibili.com/x/space/arc/search?mid={mid}&order=pubdate&pn=1&ps=5"
        r = requests.get(url, headers=headers, timeout=3).json()
        video_list = r["data"]["list"]["vlist"]
        for i in video_list:
            if re.match(r"【FF14\/时尚品鉴】第\d+期 满分攻略", i["title"]):
                return i["bvid"]
    except:
        traceback.print_exc()
    return None


def extract_nn(bvid):
    try:
        url = f"https://api.bilibili.com/x/web-interface/view?bvid={bvid}"
        r = requests.get(url, headers=headers, timeout=3).json()
        if r["code"] == 0:
            url = f"https://www.bilibili.com/video/{bvid}"
            title = r["data"]["title"]
            desc = r["data"]["desc"]
            text = desc.replace("个人攻略网站", "游玩C攻略站")
            image = r["data"]["pic"]
            res_data = {
                "url": url,
                "title": title,
                "content": text,
                "image": image,
            }
            return res_data
    except:
        traceback.print_exc()
    return None


def QQCommand_nuannuan(*args, **kwargs):
    action_list = []
    bot = kwargs["bot"]
    try:
        receive = kwargs["receive"]
        try:
            # 获取视频av号(aid)
            bvid = get_video_id(15503317)
            # 获取数据
            res_data = extract_nn(bvid)
            if not res_data:
                msg = "无法查询到有效数据，请稍后再试"
            else:
                msg = [{"type": "share", "data": res_data}]
                if receive.get("message", "").endswith("image"):
                    res_str = "\n".join([res_data["title"], res_data["content"]])
                    msg = text2img(res_str)
                    msg += res_data["url"]
                # print(msg)
        except Exception as e:
            msg = "Error: {}".format(type(e))
            traceback.print_exc()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
