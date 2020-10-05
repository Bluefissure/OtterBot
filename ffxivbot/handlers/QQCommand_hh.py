from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import sys
import os
import io
import logging
import json
import random
import requests
import urllib.request
import math
import re
import time
import traceback
import base64
from PIL import ImageFont
from PIL import Image
from PIL import ImageDraw


def search_id(glamour_id):
    try:
        glamour_url = "https://api.ffxivsc.cn/glamour/v1/getGlamourInfo?uid=&glamourId={}".format(
            glamour_id
        )
        headers = {
            "Host": "api.ffxivsc.cn",
            "Origin": "https://www.ffxivsc.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/78.0.3904.87 Safari/537.36",
            "Referer": "https://www.ffxivsc.cn/page/glamour.html?glamourId={}".format(
                glamour_id
            ),
            "Accept-Encoding": "gzip, deflate, br",
        }
        r = requests.get(glamour_url, headers=headers, timeout=5)
        r = r.json()
        flag = r["flag"]
        result = {}
        if flag == 200:
            r = r["array"][0]
            result["flag"] = 200
            result["sc"] = (
                "主手：{0:{6}<25}\t副手：{1}-{2}\n\n\n头部：{3:{6}<25}\t耳环：{4}-{5}\n\n\n".format(
                    r["glamourWeaponry"] + "-" + r["glamourWeaponryColor"],
                    r["glamourSecond"],
                    r["glamourSecondColor"],
                    r["glamourHeadgear"] + "-" + r["glamourHeadgearColor"],
                    r["glamourEarringsgear"],
                    r["glamourEarringsgearColor"],
                    chr(12288),
                    end="",
                )
                + "上衣：{0:{6}<25}\t项链：{1}-{2}\n\n\n手套：{3:{6}<25}\t手镯：{4}-{5}\n\n\n".format(
                    r["glamourBodygear"] + "-" + r["glamourBodygearColor"],
                    r["glamourNecklacegear"],
                    r["glamourNecklacegearColor"],
                    r["glamourHandgear"] + "-" + r["glamourHandgearColor"],
                    r["glamourArmillaegear"],
                    r["glamourArmillaegearColor"],
                    chr(12288),
                    end="",
                )
                + "腿部：{0:{6}<25}\t戒指：{1}-{2}\n\n\n脚部：{3:{6}<25}\t戒指：{4}-{5}".format(
                    r["glamourLeggear"] + "-" + r["glamourLeggearColor"],
                    r["glamourRingLgear"],
                    r["glamourRingLgearColor"],
                    r["glamourFootgear"] + "-" + r["glamourFootgearColor"],
                    r["glamourRingRgear"],
                    r["glamourRingRgearColor"],
                    chr(12288),
                    end="",
                )
            )
            result["race"] = r["glamourCharacter"] + "-" + r["glamourClass"]
            result["tittle"] = r["glamourTitle"] + "-ID：{}".format(glamour_id)
            result["introduction"] = r["glamourIntroduction"]
            result["img"] = r["glamourUrl"]
        else:
            result["flag"] = 400
        return result
    except Exception as e:
        return "Error: {},未能找到id信息".format(type(e))


def result_to_img(result, glamour_id, bot_version):
    try:
        if bot_version == "air" and False:
            msg = "此机器人版本为Air无法发送图片,请前往原地址查看\nhttps://www.ffxivsc.cn/page/glamour.html?glamourId={}".format(
                glamour_id
            )
        else:
            text = u"{}".format(result["sc"])
            tittle = u"{}".format(result["tittle"])
            itd = u"{}".format(result["introduction"])
            tmp = list(itd)
            t = 50
            while t < len(tmp):
                tmp.insert(t, "\n")
                t += 50
            itd = "".join(tmp)
            race = u"{}".format(result["race"])
            img = urllib.request.urlopen(result["img"])
            file = io.BytesIO(img.read())
            pic_foo = Image.open(file)
            pic_foo = pic_foo.resize((521, 1000), Image.ANTIALIAS)
            logo = Image.open(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "resources/image/logoBlack.jpg",
                )
            )
            im = Image.new("RGB", (2000, 1000), (255, 255, 255))
            im.paste(pic_foo)
            im.paste(logo, (1825, 925))
            dr = ImageDraw.Draw(im)
            font = ImageFont.truetype(
                os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "resources/font/msyh.ttc",
                ),
                28,
            )
            dr.text(
                (600, 50),
                tittle + "\n\n" + itd + "\n\n" + race + "\n\n" + text,
                font=font,
                fill="#000000",
            )
            t = (
                time.strftime("%Y-%m-%d_%H:%M:%S", time.localtime())
                + str(time.time() - int(time.time()))[2:4]
            )
            output_buffer = io.BytesIO()
            im.save(output_buffer, format="JPEG")
            byte_data = output_buffer.getvalue()
            base64_str = base64.b64encode(byte_data).decode("utf-8")
            msg = "[CQ:image,file=base64://{}]\n".format(base64_str)
        return msg
    except Exception as e:
        return "Error: {},封面图丢失,请前往原地址查看\nhttps://www.ffxivsc.cn/page/glamour.html?glamourId={}".format(
            type(e), glamour_id
        )


def search_jr(job, race, sex, sort, time, bot_version, item_name, item_flag=False):
    try:
        headers = {
            "Host": "api.ffxivsc.cn",
            "Origin": "https://www.ffxivsc.cn",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/85.0.4183.102 Safari/537.36",
            "Referer": "https://www.ffxivsc.cn/page/glamourList.html",
            "Accept-Encoding": "gzip, deflate, br",
        }
        if item_flag:
            src_url = "https://api.ffxivsc.cn/glamour/v1/librarySearchItem?language=zh&job={}&itemName={}&race={}&sex={}&sort=1&time=0".format(
                job, item_name, race, sex
            )
        else:
            src_url = "https://api.ffxivsc.cn/glamour/v1/getLibraryFilterGlamours?job={}&race={}&sex={}&sort={}&time={}&pageNum=1".format(
                job, race, sex, sort, time
            )

        r = requests.get(src_url, headers=headers, timeout=5)
        r = r.json()
        if r["flag"] == 200:
            i = random.randint(0, len(r["array"]) - 1)
            glamour_id = r["array"][i]["glamourId"]
            result = search_id(glamour_id)
            img = result_to_img(result, glamour_id, bot_version)
        else:
            print(r)
            img = "未能筛选到结果，请尝试更改筛选信息，\n职业：{}\n种族：{}\n性别：{}\n装备名称：{}".format(
                job, race, sex, item_name
            )
        return img
    except Exception as e:
        return "Error: {}".format(type(e))


def QQCommand_hh(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        bot = kwargs["bot"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        sort = "0"  # sort = "all"
        time = "0"  # time = "now"
        rank = False
        item_name = ""
        item_flag = False
        receive_msg = receive["message"].replace("/hh", "", 1).strip()
        bot_version = (
            json.loads(bot.version_info)["coolq_edition"]
            if bot.version_info != "{}"
            else "air"
        )
        if receive_msg.find("help") == 0 or receive_msg == "":
            msg = (
                "/hh [职业] [种族] [性别] : 随机返回至少一个参数的幻化\n"
                + "如：/hh 占星 or /hh 拉拉菲尔 男\n"
                + "可加参数 rank [mode] : 随机返回一个职业或种族排行榜点赞最多的幻化(可用mode: hour, week, month, all)\n"
                + "如：/hh 公肥 rank month \n"
                + "/hh [职业] [种族] [性别] item [mode] : 查询指定装备至今点赞排行榜的幻化搭配，装备名必须全名且正确(无“rank”参数)\n"
                + "如：/hh 公肥 item 巫骨低吟者短衣\n"
                + "Powered by https://www.ffxivsc.cn"
            )
        else:
            if "rank" in receive_msg:
                sort = "1"  # sort = "great"
            if "item" in receive_msg:
                item_flag = True
                item_name = receive_msg.split("item")[1].strip()
                receive_msg = (
                    receive_msg.replace("item", "", 1).replace(item_name, "", 1).strip()
                )
            receive_msg = receive_msg.replace("rank", "", 1).strip()
            receive_msg = receive_msg.replace("item", "", 1).strip()
            receive_msg_tmp = receive_msg.split(" ")
            if {"hour": "1", "week": "2", "month": "3", "all": "0"}.get(
                receive_msg_tmp[-1]
            ):
                time = {"hour": "1", "week": "2", "month": "3", "all": "0"}.get(
                    receive_msg_tmp[-1]
                )
            job = None
            race = None
            sex = None
            job_list = Screen.objects.filter(classname="job")
            for jobs in job_list:
                try:
                    job_nicknames = json.loads(jobs.nickname)["nickname"]
                except KeyError:
                    job_nicknames = []
                job_nicknames.append(jobs.name)
                job_nicknames.sort(key=lambda x: len(x), reverse=True)
                for item in job_nicknames:
                    if item in receive_msg:
                        receive_msg = receive_msg.replace(item, "", 1).strip()
                        job = jobs.id
                        break
                if job:
                    break
            race_list = Screen.objects.filter(classname="race")
            for races in race_list:
                try:
                    race_nicknames = json.loads(races.nickname)["nickname"]
                except KeyError:
                    scree_nicknames = []
                race_nicknames.append(races.name)
                race_nicknames.sort(key=lambda x: len(x), reverse=True)
                for item in race_nicknames:
                    if item in receive_msg:
                        receive_msg = receive_msg.replace(item, "", 1).strip()
                        race = races.id
                        break
                if race:
                    break
            sex_list = Screen.objects.filter(classname="sex")
            for sexs in sex_list:
                try:
                    sex_nicknames = json.loads(sexs.nickname)["nickname"]
                except KeyError:
                    sex_nicknames = []
                sex_nicknames.append(sexs.name)
                for item in sex_nicknames:
                    if item in receive_msg:
                        receive_msg = receive_msg.replace(item, "", 1).strip()
                        sex = sexs.id
                        break
                if sex:
                    break
            if not job:
                job = "0"  # job = "all"
            if not race:
                race = "0"  # race = "all"
            if not sex:
                sex = "0"  # sex = "all"
            msg = search_jr(
                job, race, sex, sort, time, bot_version, item_name, item_flag
            )
        msg = msg.strip()
        if msg:
            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
        return action_list
    except Exception as e:
        traceback.print_exc()
        msg = "尚未查询到相关信息。"
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        return action_list

