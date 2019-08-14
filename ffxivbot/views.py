# -*- coding: utf-8 -*-
import base64
import codecs
import datetime
import hmac
import html
import json
import logging
import math
import os
import random
import re
import sys
import time
import traceback
import urllib
import copy
from collections import OrderedDict
from hashlib import md5
from time import localtime, strftime

import pytz
import requests
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.core.files.base import ContentFile
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import Http404, HttpResponseRedirect, render
from django.template import Context, RequestContext, loader
from django.template.context_processors import csrf
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt

import ffxivbot.handlers as handlers
import pika
import pymysql
from asgiref.sync import async_to_sync
from bs4 import BeautifulSoup
from channels.layers import get_channel_layer
from FFXIV import settings
from ffxivbot.consumers import PikaPublisher
from ffxivbot.models import *
from ffxivbot.webapi import github_webhook, webapi
from websocket import create_connection

from .oauth_client import OAuthQQ


def ren2res(template, req, dict={}, json_res=False):
    if req.user.is_authenticated:
        qquser = req.user.qquser
        p = re.compile('^[0-9a-zA-Z_]+$')
        dict.update({'user': {
            "nickname": qquser.nickname,
            "avatar": qquser.avatar_url
        }})
    else:
        dict.update({'user': False})
    if req:
        if json_res and req.is_ajax() and req.method == 'GET':
            return JsonResponse(dict)
        return render(req, template, dict)
    else:
        return render(req, template, dict)


# Create your views here.


def tata(req):
    if req.is_ajax() and req.method == "POST":
        res_dict = {"response": "No response."}
        optype = req.POST.get("optype")
        if optype == "add_or_update_bot":
            botName = req.POST.get("botName")
            botID = req.POST.get("botID")
            ownerID = req.POST.get("ownerID")
            accessToken = req.POST.get("accessToken")
            tulingToken = req.POST.get("tulingToken")
            api_post_url = req.POST.get("api_post_url", "").strip()
            autoFriend = req.POST.get("autoFriend")
            autoInvite = req.POST.get("autoInvite")
            if len(botName) < 2:
                res_dict = {"response": "error", "msg": "机器人昵称太短"}
                return JsonResponse(res_dict)
            elif len(accessToken) < 5:
                res_dict = {"response": "error", "msg": "Access Token太短"}
                return JsonResponse(res_dict)
            elif not ownerID.strip():
                res_dict = {"response": "error", "msg": "领养者不能为空"}
                return JsonResponse(res_dict)
            bots = QQBot.objects.filter(user_id=botID)
            if not bots.exists():
                bot = QQBot(user_id=botID, access_token=accessToken)
                bot_created = True
            else:
                if bots[0].access_token != accessToken:
                    res_dict = {"response": "error", "msg": "Token错误，请确认后重试。"}
                    return JsonResponse(res_dict)
                else:
                    bot = bots[0]
                    bot_created = False
            if bot:
                bot.name = botName
                bot.owner_id = ownerID
                bot.tuling_token = tulingToken
                bot.api_post_url = api_post_url
                bot.auto_accept_friend = autoFriend and "true" in autoFriend
                bot.auto_accept_invite = autoInvite and "true" in autoInvite
                if len(QQBot.objects.all()) >= 200 and bot_created:
                    res_dict = {"response": "error", "msg": "机器人总数过多，请稍后再试"}
                    return JsonResponse(res_dict)
                bot.save()
                res_dict = {
                    "response": "success",
                    "msg": "{}({})".format(bot.name, bot.user_id) + ("添加" if bot_created else "更新") + "成功，Token为:",
                    "token": bot.access_token,
                }
            return JsonResponse(res_dict)
        else:
            bot_id = req.POST.get("id")
            token = req.POST.get("token")
            try:
                bot = QQBot.objects.get(id=bot_id, access_token=token)
            except Exception as e:
                if "QQBot matching query does not exist" in str(e):
                    res_dict = {"response": "error", "msg": "Token错误，请确认后重试。"}
                else:
                    res_dict = {"response": "error", "msg": str(e)}
                return JsonResponse(res_dict)
            if optype == "switch_public":
                bot.public = not bot.public
                bot.save()
                res_dict["response"] = "success"
            elif optype == "del_bot":
                bot.delete()
                res_dict["response"] = "success"
            elif optype == "download_conf":
                response = HttpResponse(content_type="application/octet-stream")
                response[
                    "Content-Disposition"
                ] = 'attachment; filename="{}.json"'.format(bot.user_id)
                bot_conf = json.loads(
                    '{"host":"0.0.0.0","port":5700,"use_http":false,"ws_host":"0.0.0.0","ws_port":6700,"use_ws":false,"ws_reverse_api_url":"ws://111.231.102.248/ws_api/","ws_reverse_event_url":"ws://111.231.102.248/ws_event/","use_ws_reverse":"yes","ws_reverse_reconnect_interval":5000,"ws_reverse_reconnect_on_code_1000":"yes","post_url":"","access_token":"SECRET","secret":"","post_message_format":"string","serve_data_files":false,"update_source":"github","update_channel":"stable","auto_check_update":false,"auto_perform_update":false,"thread_pool_size":4,"server_thread_pool_size":1,"show_log_console":false,"enable_backward_compatibility":true}'
                )
                bot_conf["secret"] = bot.access_token
                response.write(json.dumps(bot_conf, indent=4))
                return response
        return JsonResponse(res_dict)

    bots = QQBot.objects.all()
    bot_list = []
    for bot in bots:
        bb = {}
        version_info = json.loads(bot.version_info)
        coolq_edition = (
            version_info["coolq_edition"]
            if version_info and "coolq_edition" in version_info.keys()
            else ""
        )
        if coolq_edition != "":
            coolq_edition = coolq_edition[0].upper() + coolq_edition[1:]
        friend_list = json.loads(bot.friend_list)
        friend_num = (
            len(friend_list["friends"])
            if friend_list and "friends" in friend_list.keys()
            else "-1"
        )
        group_list = json.loads(bot.group_list)
        group_num = len(group_list)
        bb["name"] = bot.name
        if bot.public:
            bb["user_id"] = bot.user_id
        else:
            mid = len(bot.user_id) // 2
            user_id = bot.user_id[: mid - 2] + "*" * 4 + bot.user_id[mid + 2:]
            bb["user_id"] = user_id
        bb["group_num"] = group_num
        bb["friend_num"] = friend_num
        bb["coolq_edition"] = coolq_edition
        bb["owner_id"] = bot.owner_id
        bb["online"] = time.time() - bot.event_time < 300
        bb["id"] = bot.id
        bb["public"] = bot.public
        bb["autoinvite"] = bot.auto_accept_invite
        bb["autofriend"] = bot.auto_accept_friend
        bot_list.append(bb)
    return ren2res("tata.html", req, {"bots": bot_list})


def quest(req):
    if req.is_ajax() and req.method == "POST":
        res_dict = {"response": "No response."}
        optype = req.POST.get("optype")
        if optype == "search_quest":
            max_iter = req.POST.get("max_iter")
            main_quest = req.POST.get("main_quest")
            main_quest = main_quest and "true" in main_quest
            sub_quest = req.POST.get("sub_quest")
            sub_quest = sub_quest and "true" in sub_quest
            start_quest = req.POST.get("start_quest").replace("任务:", "", 1)
            start_quest = PlotQuest.objects.filter(name=start_quest)
            start_quest = start_quest[0] if start_quest else None
            end_quest = req.POST.get("end_quest")
            end_quest = PlotQuest.objects.filter(name=end_quest)
            end_quest = end_quest[0] if end_quest else None
            max_iter = req.POST.get("max_iter")
            print("main_quest:{}".format(main_quest))
            print("sub_quest:{}".format(sub_quest))
            print("start_quest:{}".format(start_quest))
            quest_dict = {}
            tmp_edge_list = []
            edge_list = []
            if not start_quest and not end_quest:
                res_dict["response"] = "找不到对应任务"
            elif start_quest and end_quest:
                res_dict["response"] = "TODO: Double Quest Search"
            else:
                single_quest = start_quest or end_quest
                search_list = []
                search_iter = 0
                search_list.append((single_quest, 1, 1))
                search_list.append((single_quest, 2, 1))
                if (single_quest.is_main_scenario() and not main_quest) or (
                        not single_quest.is_main_scenario() and not sub_quest
                ):
                    res_dict["response"] = "查询任务类别与所选类别不符，清选择正确的类别。"
                    return JsonResponse(res_dict)
                done_cnt = 0
                tot_cnt = 0
                while search_list and search_iter <= min(int(max_iter), 1000):
                    try:
                        (now_quest, direction, search_iter) = search_list[0]
                        search_list = search_list[1:]
                        if single_quest.is_main_scenario():
                            if not main_quest:
                                continue
                        elif not sub_quest:
                            continue
                        if direction == 2:
                            done_cnt += 1
                        now_quest_dict = {
                            "description": "",
                            "startnpc": "",
                            "endnpc": "",
                        }
                        if now_quest.name not in quest_dict.keys():
                            quest_dict[now_quest.name] = now_quest_dict
                        else:
                            if now_quest.name != single_quest.name:
                                continue
                        if not now_quest.endpoint:
                            if direction == 1:
                                for quest in now_quest.suf_quests.all():
                                    if (quest.is_main_scenario() and main_quest) or \
                                            (not quest.is_main_scenario() and sub_quest):
                                        if quest.name not in quest_dict.keys():
                                            search_list.append((quest, 1, search_iter + 1))
                                        edge = {"from": now_quest.name, "to": quest.name}
                                        if edge not in edge_list:
                                            tmp_edge_list.append(edge)
                        if not now_quest.endpoint or (
                                now_quest.endpoint and now_quest.name == single_quest.name
                        ):
                            if direction == 2:
                                for quest in now_quest.pre_quests.all():
                                    if (quest.is_main_scenario() and main_quest) or \
                                            (not quest.is_main_scenario() and sub_quest):
                                        if quest.name not in quest_dict.keys():
                                            search_list.append((quest, 2, search_iter + 1))
                                        edge = {"from": quest.name, "to": now_quest.name}
                                        if edge not in edge_list:
                                            tmp_edge_list.append(edge)
                    except Exception as e:
                        print(e)
                for edge in tmp_edge_list:
                    if (
                            edge["from"] in quest_dict.keys()
                            and edge["to"] in quest_dict.keys()
                    ):
                        edge_list.append(edge)
                quest_dict[single_quest.name]["style"] = "fill: #7f7"
                tot_cnt = len(quest_dict.keys())
                perc = done_cnt / tot_cnt * 100
                perc = min(100, perc)
                perc = max(0, perc)
                res_dict["percentage"] = perc
                res_dict["quest_dict"] = quest_dict
                res_dict["quest_dict"] = quest_dict
                res_dict["edge_list"] = edge_list
                res_dict["response"] = "success"
        return JsonResponse(res_dict)
    return ren2res("quest.html", req, {})


def image(req):
    if req.is_ajax() and req.method == "POST":
        res_dict = {"response": "No response."}
        json_req = json.loads(req.body)
        optype = json_req.get("optype")
        if optype == "get_images":
            cat = json_req.get("category", "")
            cached_images = json_req.get("cached_images", [])
            image_filter = Image.objects.order_by('?').exclude(name__in=cached_images)
            if cat:
                image_filter = image_filter.filter(Q(key__contains=cat) | Q(add_by__user_id__contains=cat))
            images = list(
                map(
                    lambda x: {
                        "name": x.name,
                        "url": "https://i.loli.net" + x.path,
                        "category": x.key,
                        "info": "Name:{}\nCategory:{}\nUploader:{}".format(x.name, x.key, x.add_by)
                    },
                    list(image_filter[:30]),
                )
            )
            res_dict = {"images": images, "response": "success"}
        else:
            res_dict = {"msg": "not support", "response": "error"}
        return JsonResponse(res_dict)

    return ren2res("image.html", req, {})


def quest_tooltip(req):
    quest_id = req.GET.get("id", 0)
    nocache = req.GET.get("nocache", "False") == "True"
    res_type = req.GET.get("type", "web")
    print("quest_id:{}".format(quest_id))
    try:
        if quest_id:
            try:
                quest = PlotQuest.objects.get(id=quest_id)
            except PlotQuest.DoesNotExist:
                return HttpResponse("No such quest", status=500)
            else:
                if res_type == "web":
                    if quest.tooltip_html == "" or nocache:
                        r = requests.get(
                            "https://ff14.huijiwiki.com/ff14/api.php?format=json&action=parse&disablelimitreport=true&prop=text&title=%E9%A6%96%E9%A1%B5&smaxage=86400&maxage=86400&text=%7B%7B%E4%BB%BB%E5%8A%A1%2F%E6%B5%AE%E5%8A%A8%E6%91%98%E8%A6%81%7C{}%7D%7D".format(
                                quest_id
                            ))
                        r_json = r.json()
                        # print(r_json)
                        html = r_json["parse"]["text"]["*"]
                        html = html.replace("class=\"tooltip-item\"", "class=\"tooltip-item\" id=\"tooltip\"", 1)
                        html = html.replace("href=\"/", "href=\"https://ff14.huijiwiki.com/")
                        soup = BeautifulSoup(html, 'html.parser')
                        quest_name = soup.p.span.string
                        a = soup.new_tag('a', href='https://ff14.huijiwiki.com/wiki/%E4%BB%BB%E5%8A%A1:{}'.format(
                            urllib.parse.quote(quest_name)))
                        a.string = quest_name
                        soup.p.span.string = ""
                        soup.p.span.append(a)
                        html = str(soup)
                        quest.tooltip_html = html
                        quest.save(update_fields=["tooltip_html"])
                    else:
                        html = quest.tooltip_html
                    return ren2res("quest_tooltip.html", req, {"parsed_html": html})
                elif res_type == "img" or res_type == "image":
                    return HttpResponse("TODO", status=500)
    except KeyError:
        return HttpResponse("KeyError", status=500)
    return HttpResponse(status=500)


def get_nm_id(tracker, nm_name):
    if tracker == "ffxiv-eureka":
        name_id = {
            "科里多仙人刺": 1,
            "常风领主": 2,
            "忒勒斯": 3,
            "常风皇帝": 4,
            "卡利斯托": 5,
            "群偶": 6,
            "哲罕南": 7,
            "阿米特": 8,
            "盖因": 9,
            "庞巴德": 10,
            "塞尔凯特": 11,
            "武断魔花茱莉卡": 12,
            "白骑士": 13,
            "波吕斐摩斯": 14,
            "阔步西牟鸟": 15,
            "极其危险物质": 16,
            "法夫纳": 17,
            "阿玛洛克": 18,
            "拉玛什图": 19,
            "帕祖祖": 20,
            "雪之女王": 21,
            "塔克西姆": 22,
            "灰烬龙": 23,
            "异形魔虫": 24,
            "安娜波": 25,
            "白泽": 26,
            "雪屋王": 27,
            "阿萨格": 28,
            "苏罗毗": 29,
            "亚瑟罗王": 30,
            "唇亡齿寒": 31,
            "优雷卡圣牛": 32,
            "哈达约什": 33,
            "荷鲁斯": 34,
            "总领安哥拉": 35,
            "复制魔花凯西": 36,
            "娄希": 37,
            "琉科西亚": 38,
            "佛劳洛斯": 39,
            "诡辩者": 40,
            "格拉菲亚卡内": 41,
            "阿斯卡拉福斯": 42,
            "巴钦大公爵": 43,
            "埃托洛斯": 44,
            "来萨特": 45,
            "火巨人": 46,
            "伊丽丝": 47,
            "佣兵雷姆普里克斯": 48,
            "闪电督军": 49,
            "樵夫杰科": 50,
            "明眸": 51,
            "阴·阳": 52,
            "斯库尔": 53,
            "彭忒西勒亚": 54,
            "卡拉墨鱼": 55,
            "剑齿象": 56,
            "摩洛": 57,
            "皮艾萨邪鸟": 58,
            "霜鬃猎魔": 59,
            "达佛涅": 60,
            "戈尔德马尔王": 61,
            "琉刻": 62,
            "巴龙": 63,
            "刻托": 64,
            "起源守望者": 65,
        }
        for (k, v) in name_id.items():
            if k in nm_name:
                return v
    if tracker == "ffxivsc":
        name_id = {
            "科里多仙人刺": {"level": 1, "type": 1},
            "常风领主": {"level": 2, "type": 1},
            "忒勒斯": {"level": 3, "type": 1},
            "常风皇帝": {"level": 4, "type": 1},
            "卡利斯托": {"level": 5, "type": 1},
            "群偶": {"level": 6, "type": 1},
            "哲罕南": {"level": 7, "type": 1},
            "阿米特": {"level": 8, "type": 1},
            "盖因": {"level": 9, "type": 1},
            "庞巴德": {"level": 10, "type": 1},
            "塞尔凯特": {"level": 11, "type": 1},
            "武断魔花茱莉卡": {"level": 12, "type": 1},
            "白骑士": {"level": 13, "type": 1},
            "波吕斐摩斯": {"level": 14, "type": 1},
            "阔步西牟鸟": {"level": 15, "type": 1},
            "极其危险物质": {"level": 16, "type": 1},
            "法夫纳": {"level": 17, "type": 1},
            "阿玛洛克": {"level": 18, "type": 1},
            "拉玛什图": {"level": 19, "type": 1},
            "帕祖祖": {"level": 20, "type": 1},
            "雪之女王": {"level": 20, "type": 2},
            "塔克西姆": {"level": 21, "type": 2},
            "灰烬龙": {"level": 22, "type": 2},
            "异形魔虫": {"level": 23, "type": 2},
            "安娜波": {"level": 24, "type": 2},
            "白泽": {"level": 25, "type": 2},
            "雪屋王": {"level": 26, "type": 2},
            "阿萨格": {"level": 27, "type": 2},
            "苏罗毗": {"level": 28, "type": 2},
            "亚瑟罗王": {"level": 29, "type": 2},
            "唇亡齿寒": {"level": 30, "type": 2},
            "优雷卡圣牛": {"level": 31, "type": 2},
            "哈达约什": {"level": 32, "type": 2},
            "荷鲁斯": {"level": 33, "type": 2},
            "总领安哥拉": {"level": 34, "type": 2},
            "复制魔花凯西": {"level": 35, "type": 2},
            "娄希": {"level": 36, "type": 2},
            "琉科西亚": {"level": 35, "type": 3},
            "佛劳洛斯": {"level": 36, "type": 3},
            "诡辩者": {"level": 37, "type": 3},
            "格拉菲亚卡内": {"level": 38, "type": 3},
            "阿斯卡拉福斯": {"level": 39, "type": 3},
            "巴钦大公爵": {"level": 40, "type": 3},
            "埃托洛斯": {"level": 41, "type": 3},
            "来萨特": {"level": 42, "type": 3},
            "火巨人": {"level": 43, "type": 3},
            "伊丽丝": {"level": 44, "type": 3},
            "佣兵雷姆普里克斯": {"level": 45, "type": 3},
            "闪电督军": {"level": 46, "type": 3},
            "樵夫杰科": {"level": 47, "type": 3},
            "明眸": {"level": 48, "type": 3},
            "阴·阳": {"level": 49, "type": 3},
            "斯库尔": {"level": 50, "type": 3},
            "彭忒西勒亚": {"level": 51, "type": 3},
            "卡拉墨鱼": {"level": 50, "type": 4},
            "剑齿象": {"level": 51, "type": 4},
            "摩洛": {"level": 52, "type": 4},
            "皮艾萨邪鸟": {"level": 53, "type": 4},
            "霜鬃猎魔": {"level": 54, "type": 4},
            "达佛涅": {"level": 55, "type": 4},
            "戈尔德马尔王": {"level": 56, "type": 4},
            "琉刻": {"level": 57, "type": 4},
            "巴龙": {"level": 58, "type": 4},
            "刻托": {"level": 59, "type": 4},
            "起源守望者": {"level": 60, "type": 4},
        }
        for (k, v) in name_id.items():
            if k in nm_name:
                return v
        return {"level": -1, "type": -1}
    return -1


def handle_hunt_msg(msg):
    if msg.find("hunt") != 0:
        return msg
    new_msg = msg.replace("hunt", "", 1)
    print(new_msg)
    segs = new_msg.split("|")
    print(segs)
    if len(segs) < 3:
        return msg
    map_name = segs[0].strip()
    map_pos = segs[1].strip()
    ts = Territory.objects.filter(name__icontains=map_name.strip())
    if ts.exists():
        t = ts[0]
        x, y = map(float, map_pos.replace("(", "").replace(")", "").split(","))
        new_msg += "\nMap:https://map.wakingsands.com/#f=mark&x={}&y={}&id={}".format(
            x, y, t.mapid
        )
    print(new_msg)
    return new_msg


@csrf_exempt
def api(req):
    httpresponse = None
    if req.method == "POST":
        tracker = req.GET.get("tracker")
        trackers = tracker.split(",")
        print("tracker:{}".format(tracker))
        if tracker:
            if "ffxiv-eureka" in trackers:
                instance = req.GET.get("instance")
                password = req.GET.get("password")
                print("ffxiv-eureka {}:{}".format(instance, password))
                if instance and password:
                    nm_name = req.POST.get("text")
                    if nm_name:
                        nm_id = get_nm_id("ffxiv-eureka", nm_name)
                        print("nm_name:{} id:{}".format(nm_name, nm_id))
                        if nm_id > 0:
                            print("nm_name:{} nm_id:{}".format(nm_name, nm_id))
                            # ws = create_connection("wss://ffxiv-eureka.com/socket/websocket?vsn=2.0.0")
                            ws = create_connection(
                                "wss://ffxiv-eureka.com/socket/websocket?vsn=2.0.0"
                            )
                            msg = '["1","1","instance:{}","phx_join",{{"password":"{}"}}]'.format(
                                instance, password
                            )
                            # print(msg)
                            ws.send(msg)
                            msg = '["1","2","instance:{}","set_kill_time",{{"id":{},"time":{}}}]'.format(
                                instance, nm_id, int(time.time() * 1000)
                            )
                            # print(msg)
                            ws.send(msg)
                            ws.close()
                            httpresponse = HttpResponse("OK", status=200)
                    else:
                        print("no nm_name")
            if "ffxivsc" in trackers:
                key = req.GET.get("key")
                # print("ffxiv-eureka {}:{}".format(instance,password))
                if key:
                    nm_name = req.POST.get("text")
                    if nm_name:
                        nm_level_type = get_nm_id("ffxivsc", nm_name)
                        if int(nm_level_type["type"]) > 0:
                            url = (
                                "https://nps.ffxivsc.cn/lobby/addKillTime"
                            )
                            post_data = {
                                "killTime": strftime(
                                    "%Y-%m-%d %H:%M", time.localtime()
                                ),
                                "level": "{}".format(nm_level_type["level"]),
                                "key": key,
                                "type": "{}".format(nm_level_type["type"]),
                            }
                            r = requests.post(url=url, data=post_data)
                            httpresponse = HttpResponse(r)
                    else:
                        print("no nm_name")
            if "qq" in trackers:
                bot_qq = req.GET.get("bot_qq")
                qq = req.GET.get("qq")
                token = req.GET.get("token")
                group_id = req.GET.get("group")
                print("bot: {} qq:{} token:{}".format(bot_qq, qq, token))
                if bot_qq and qq and token:
                    bot = None
                    qquser = None
                    group = None
                    api_rate_limit = True
                    try:
                        bot = QQBot.objects.get(user_id=bot_qq)
                    except QQBot.DoesNotExist:
                        print("bot {} does not exist".format(bot_qq))
                    try:
                        qquser = QQUser.objects.get(user_id=qq, bot_token=token)
                        if time.time() < qquser.last_api_time + qquser.api_interval:
                            api_rate_limit = False
                            print("qquser {} api rate limit exceed".format(qq))
                        qquser.last_api_time = int(time.time())
                        qquser.save(update_fields=["last_api_time"])
                    except QQUser.DoesNotExist:
                        print("qquser {}:{} auth fail".format(qq, token))
                    if bot and qquser and api_rate_limit:
                        channel_layer = get_channel_layer()
                        msg = req.POST.get("text")
                        reqbody = req.body
                        try:
                            if reqbody:
                                reqbody = reqbody.decode()
                                reqbody = json.loads(reqbody)
                                msg = msg or reqbody.get("content")
                                msg = re.compile(
                                    "[\\x00-\\x08\\x0b-\\x0c\\x0e-\\x1f]"
                                ).sub(" ", msg)
                        except BaseException:
                            pass
                        if not msg:
                            msg = github_webhook(req)
                        if not msg:
                            print("Can't get msg from request:{}:{}".format(req, reqbody))
                            httpresponse = HttpResponse("Can't get message", status=500)
                        else:
                            print("body:{}".format(req.body.decode()))
                            if group_id:
                                try:
                                    group = QQGroup.objects.get(group_id=group_id)
                                    group_push_list = [
                                        user["user_id"]
                                        for user in json.loads(group.member_list)
                                        if (
                                                user["role"] == "owner"
                                                or user["role"] == "admin"
                                        )
                                    ]
                                    print("group push list:{}".format(group_push_list))
                                except QQGroup.DoesNotExist:
                                    print("group:{} does not exist".format(group_id))
                            msg = handle_hunt_msg(msg)
                            if (
                                    group
                                    and group.api
                                    and int(qquser.user_id) in group_push_list
                            ):
                                jdata = {
                                    "action": "send_group_msg",
                                    "params": {
                                        "group_id": group.group_id,
                                        "message": "Message from [CQ:at,qq={}]:\n{}".format(
                                            qquser.user_id, msg
                                        ),
                                    },
                                    "echo": "",
                                }
                            else:
                                jdata = {
                                    "action": "send_private_msg",
                                    "params": {"user_id": qquser.user_id, "message": msg},
                                    "echo": "",
                                }
                            if not bot.api_post_url:
                                async_to_sync(channel_layer.send)(
                                    bot.api_channel_name,
                                    {"type": "send.event", "text": json.dumps(jdata)},
                                )
                            else:
                                url = os.path.join(bot.api_post_url,
                                                   "{}?access_token={}".format(jdata["action"], bot.access_token))
                                headers = {'Content-Type': 'application/json'}
                                r = requests.post(url=url, headers=headers, data=json.dumps(jdata["params"]))
                                if r.status_code != 200:
                                    logging.error(r.text)
                            httpresponse = HttpResponse("OK", status=200)
            if "hunt" in trackers:
                qq = req.GET.get("qq")
                token = req.GET.get("token")
                group_id = req.GET.get("group")
                bot_qq = req.GET.get("bot_qq")
                print("qq:{} token:{}, group:{}".format(qq, token, group_id))
                if bot_qq and qq and token:
                    qquser = None
                    group = None
                    api_rate_limit = True
                    try:
                        bot = QQBot.objects.get(user_id=bot_qq)
                        qquser = QQUser.objects.get(user_id=qq, bot_token=token)
                        if time.time() < qquser.last_api_time + qquser.api_interval:
                            api_rate_limit = False
                            print("qquser {} api rate limit exceed".format(qq))
                        httpresponse = HttpResponse("User API rate limit exceed", status=500)
                    except QQUser.DoesNotExist:
                        print("qquser {}:{} auth fail".format(qq, token))
                    except QQBot.DoesNotExist:
                        print("bot {} does not exist".format(bot_qq))
                    else:
                        channel_layer = get_channel_layer()
                        try:
                            reqbody = json.loads(req.body.decode())
                        except BaseException as e:
                            print(e)
                        else:
                            print("reqbody:{}".format(reqbody))
                            try:
                                hunt_group = HuntGroup.objects.get(group__group_id=group_id)
                                group = hunt_group.group
                                group_push_list = [
                                    user["user_id"]
                                    for user in json.loads(group.member_list)
                                ]
                                assert int(qquser.user_id) in group_push_list, "You're not in the group member list"
                                monster_name = reqbody["monster"]
                                zone_name = reqbody["zone"]
                                zone_name = zone_name.replace(chr(57521), "").replace(chr(57522), "2").replace(
                                    chr(57523), "3")
                                monster = Monster.objects.get(cn_name=monster_name)
                                world_name = reqbody["world"]
                                timestamp = int(reqbody["time"])
                                server = Server.objects.get(name=world_name)
                                # handle instances
                                if str(monster.territory) in zone_name:  # "ZoneName2", "ZoneName"
                                    if str(monster.territory) != zone_name:  # "ZoneName2"
                                        monster_name = zone_name.replace(str(monster.territory),
                                                                         monster_name)  # "ZoneName2" -> "MonsterName2"
                                        monster = Monster.objects.get(cn_name=monster_name)
                                print("Get HuntLog info:\nmonster:{}\nserver:{}".format(monster, server))
                                if HuntLog.objects.filter(
                                        monster=monster,
                                        server=server,
                                        hunt_group=hunt_group,
                                        log_type="kill",
                                        time__gt=timestamp - 60).exists():
                                    msg = "{}——\"{}\" 已在一分钟内记录上报，此次API调用被忽略".format(hunt_log.server, monster,
                                                                                    time.strftime("%Y-%m-%d %H:%M:%S",
                                                                                                  time.localtime(
                                                                                                      timestamp))
                                                                                    )
                                else:
                                    hunt_log = HuntLog(
                                        monster=monster,
                                        hunt_group=hunt_group,
                                        server=server,
                                        log_type="kill",
                                        time=timestamp
                                    )
                                    hunt_log.save()
                                    msg = "{}——\"{}\" 击杀时间: {}".format(hunt_log.server, monster, 
                                            time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(timestamp))
                                        )
                                    at_msg = "[CQ:at,qq={}]".format(qquser.user_id) if req.GET.get("at", "true")=="true" else str(qquser.user_id)
                                    msg = at_msg + "通过API更新了如下HuntLog:\n{}".format(msg)
                                jdata = {
                                    "action": "send_group_msg",
                                    "params": {
                                        "group_id": hunt_group.group.group_id,
                                        "message": msg,
                                    },
                                    "echo": "",
                                }
                                if not bot.api_post_url:
                                    async_to_sync(channel_layer.send)(
                                        bot.api_channel_name,
                                        {"type": "send.event", "text": json.dumps(jdata)},
                                    )
                                else:
                                    url = os.path.join(bot.api_post_url,
                                                       "{}?access_token={}".format(jdata["action"], bot.access_token))
                                    headers = {'Content-Type': 'application/json'}
                                    r = requests.post(url=url, headers=headers, data=json.dumps(jdata["params"]))
                                    if r.status_code != 200:
                                        logging.error(r.text)
                                httpresponse = HttpResponse(status=200)
                            except HuntGroup.DoesNotExist:
                                print("HuntGroup:{} does not exist".format(group_id))
                                httpresponse = HttpResponse("HuntGroup:{} does not exist".format(group_id), status=500)
                            except Monster.DoesNotExist:
                                print("Monster:{} does not exist".format(monster_name))
                                httpresponse = HttpResponse("Monster:{} does not exist".format(monster_name),
                                                            status=500)
                            except Server.DoesNotExist:
                                print("Server:{} does not exist".format(world_name))
                                httpresponse = HttpResponse("Server:{} does not exist".format(world_name), status=500)
                            except AssertionError as e:
                                print(str(e))
                                httpresponse = HttpResponse(str(e), status=500)
                else:
                    httpresponse = HttpResponse("Missing URL parameters", status=500)
            if "webapi" in trackers:
                qq = req.GET.get("qq")
                token = req.GET.get("token")
                print("qq:{}\ntoken:{}".format(qq, token))
                if qq and token:
                    qquser = None
                    try:
                        qquser = QQUser.objects.get(user_id=qq, bot_token=token)
                    except QQUser.DoesNotExist:
                        res_dict = {
                            "response": "error",
                            "msg": "Invalid API token",
                            "rcode": "101",
                        }
                        return JsonResponse(res_dict)
                    if qquser:
                        res_dict = webapi(req)
                        return JsonResponse(res_dict)
                else:
                    res_dict = {
                        "response": "error",
                        "msg": "Invalid request",
                        "rcode": "100",
                    }
                    return JsonResponse(res_dict)
                return HttpResponse("Default API Error, contact dev please", status=500)
    return httpresponse if httpresponse else HttpResponse("Default API Error, contact dev please", status=500)


FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", settings.BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)
pub = PikaPublisher()
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


@csrf_exempt
def qqpost(req):
    try:
        # print("first request headers:")
        # print(req.META)
        receive = json.loads(req.body.decode())
        receive["reply_api_type"] = "http"
        text_data = json.dumps(receive)
        self_id = received_sig = req.META.get("HTTP_X_SELF_ID", "NULL")
        error_msg = "Request not handled"
        try:
            bot = QQBot.objects.get(user_id=self_id)
            assert bot.api_post_url
        except QQBot.DoesNotExist:
            # print("bot {} does not exist".format(self_id))
            error_msg = "Bot {} does not exist".format(self_id)
        except AssertionError:
            # print("bot {} does not provide api url".format(self_id))
            error_msg = "Bot {} does not provide api url".format(self_id)
        else:
            sig = hmac.new(str(bot.access_token).encode(), req.body, 'sha1').hexdigest()
            received_sig = req.META.get("HTTP_X_SIGNATURE", "NULL")[len('sha1='):]
            # print(req.META)
            # print("sig:{}\nreceived_sig:{}".format(sig, received_sig))
            if (sig == received_sig):
                # print("QQBot {}:{} authencation success".format(bot, self_id))
                if "post_type" in receive.keys():
                    bot.event_time = int(time.time())
                    bot.save(update_fields=["event_time"])
                    config = json.load(open(CONFIG_PATH, encoding="utf-8"))
                    already_reply = False
                    try:
                        self_id = receive["self_id"]
                        if "message" in receive.keys():
                            priority = 1
                            if isinstance(receive["message"], list):
                                tmp_msg = ""
                                for msg_seg in receive["message"]:
                                    if msg_seg["type"] == "text":
                                        tmp_msg += msg_seg["data"]["text"]
                                    elif msg_seg["type"] == "image":
                                        tmp_msg += "[CQ:image,file={}]".format(msg_seg["data"]["url"])
                                    elif "face" in msg_seg["type"]:
                                        tmp_msg += "[CQ:{},id={}]".format(msg_seg["type"], msg_seg["data"]["id"])
                                    elif msg_seg["type"] == "at":
                                        tmp_msg += "[CQ:at,qq={}]".format(msg_seg["data"]["qq"])
                                receive["message"] = tmp_msg
                            if receive["message"].startswith("/") or receive[
                                "message"
                            ].startswith("\\"):
                                # print(receive["message"])
                                priority += 1
                                bot.save(update_fields=["event_time"])
                                receive["consumer_time"] = time.time()
                                text_data = json.dumps(receive)
                                pub.send(text_data, priority)
                                return HttpResponse("Request sent to MQ", status=200)
                            else:
                                push_to_mq = False
                                if "group_id" in receive:
                                    group_id = receive["group_id"]
                                    (group, group_created) = QQGroup.objects.get_or_create(
                                        group_id=group_id
                                    )
                                    push_to_mq = "[CQ:at,qq={}]".format(self_id) in receive[
                                        "message"
                                    ] or (
                                                         (group.repeat_ban > 0)
                                                         or (group.repeat_length > 1 and group.repeat_prob > 0)
                                                 )
                                    # push_to_mq = "[CQ:at,qq={}]".format(self_id) in receive["message"]
                                if push_to_mq:
                                    receive["consumer_time"] = time.time()
                                    text_data = json.dumps(receive)
                                    pub.send(text_data, priority)
                                    return HttpResponse("Request sent to MQ", status=200)
                            return HttpResponse("Request message omitted", status=200)

                        if receive["post_type"] == "request" or receive["post_type"] == "event":
                            priority = 3
                            text_data = json.dumps(receive)
                            pub.send(text_data, priority)
                            return HttpResponse("Request sent to MQ", status=200)

                    except Exception as e:
                        traceback.print_exc()
                else:
                    bot.api_time = int(time.time())
                    bot.save(update_fields=["api_time"])
                    if int(receive["retcode"]) != 0:
                        if int(receive["retcode"]) == 1 and receive["status"] == "async":
                            print("API waring:" + text_data)
                        else:
                            print("API error:" + text_data)
                    if "echo" in receive.keys():
                        echo = receive["echo"]
                        LOGGER.debug("echo:{} received".format(receive["echo"]))
                        if echo.find("get_group_member_list") == 0:
                            group_id = echo.replace("get_group_member_list:", "").strip()
                            try:
                                # group = QQGroup.objects.select_for_update().get(group_id=group_id)
                                group = QQGroup.objects.get(group_id=group_id)
                                member_list = (
                                    json.dumps(receive["data"]) if receive["data"] else "[]"
                                )
                                group.member_list = member_list
                                group.save(update_fields=["member_list"])
                                # await send_message("group", group_id, "群成员信息刷新成功")
                            except QQGroup.DoesNotExist:
                                print("QQGroup.DoesNotExist:{}".format(group_id))
                                return HttpResponse(status=200)
                            LOGGER.debug("group %s member updated" % (group.group_id))
                        if echo.find("get_group_list") == 0:
                            bot.group_list = json.dumps(receive["data"])
                            bot.save(update_fields=["group_list"])
                        if echo.find("_get_friend_list") == 0:
                            # friend_list = echo.replace("_get_friend_list:","").strip()
                            bot.friend_list = json.dumps(receive["data"])
                            bot.save(update_fields=["friend_list"])
                        if echo.find("get_version_info") == 0:
                            bot.version_info = json.dumps(receive["data"])
                            bot.save(update_fields=["version_info"])
                        if echo.find("get_status") == 0:
                            user_id = echo.split(":")[1]
                            if not receive["data"] or not receive["data"]["good"]:
                                print(
                                    "bot:{} not good at time:{}".format(
                                        user_id, int(time.time())
                                    )
                                )
                            else:
                                LOGGER.debug(
                                    "bot:{} Universal heartbeat at time:{}".format(
                                        user_id, int(time.time())
                                    )
                                )
                    # bot.save()
            else:
                return HttpResponse("Wrong HTTP_X_SIGNATURE", status=500)
        return HttpResponse(error_msg, status=500)
    except Exception as e:
        traceback.print_exc()
        # print("request body:")
        # print(req.body.decode())
        return HttpResponse("Server error:{}".format(type(e)), status=500)


def login(req):
    if req.method == 'GET':
        if req.user.is_anonymous:
            if req.GET.get('next'):
                req.session['next'] = req.GET.get('next')
            return ren2res("login.html", req, {})
        else:
            return HttpResponseRedirect("/tata")
    elif req.method == 'POST':
        user = auth.authenticate(username=req.POST.get('Email'), password=req.POST.get('Password'))
        if user:
            auth.login(req, user)
            next = req.session.get('next', '/tata')
            return HttpResponseRedirect(next)
        else:
            return ren2res("login.html", req, {'err': "用户名或密码错误！"})


def logout(req):
    auth.logout(req)
    return HttpResponseRedirect('/')


def qq_login(req):
    oauth_qq = OAuthQQ(settings.QQ_APP_ID, settings.QQ_KEY, settings.QQ_RECALL_URL)
    url = oauth_qq.get_auth_url()
    return HttpResponseRedirect(url)


def qq_check(req):
    code = req.GET.get('code', None)
    authqq = OAuthQQ(settings.QQ_APP_ID, settings.QQ_KEY, settings.QQ_RECALL_URL)
    access_token = authqq.get_access_token(code)
    time.sleep(0.05)
    qq_openid = authqq.get_open_id()
    try:
        qquser = QQUser.objects.get(open_id=qq_openid)
        user = qquser.dbuser
        auth.login(req, user)
        next = req.session.get('next', '/tata')
        return HttpResponseRedirect(next)
    except QQUser.DoesNotExist:
        if req.user.is_anonymous:
            return HttpResponseRedirect(
                "/register/?err=%E8%AF%B7%E9%A6%96%E5%85%88%E6%B3%A8%E5%86%8C%E8%B4%A6%E6%88%B7%E5%B9%B6%E7%BB%91%E5%AE%9AQQ")
        else:
            user = req.user
            qquser = user.qquser
            qqinfo = authqq.get_qq_info()
            qquser.open_id = qq_openid
            if qqinfo.get("ret", -1) == 0:
                qquser.nickname = qqinfo.get("nickname")
                qquser.avatar_url = qqinfo.get("figureurl_qq")
            qquser.save()
            next = req.session.get('next', '/tata')
            return HttpResponseRedirect(next)
    return HttpResponseRedirect("/tata")


def register(req):
    if req.method == 'GET':
        req_dict = {}
        if req.GET.get('err'):
            req_dict.update({'err': req.GET.get('err')})
        if req.user.is_anonymous:
            if req.GET.get('next'):
                req.session['next'] = req.GET.get('next')
            return ren2res('register.html', req, req_dict)
        else:
            return HttpResponseRedirect('/')
    elif req.method == 'POST':
        email = req.POST.get('Email')
        vcode = req.POST.get('Verification Code')
        emailresult = User.objects.filter(username=email)
        p = re.compile('^\d+@qq\.com$')
        if not email:
            return ren2res('register.html', req, {'err': "Email格式错误"})
        elif p.match(email) == None:
            return ren2res('register.html', req, {'err': "目前仅支持QQ邮箱注册"})
        elif emailresult.exists():
            return ren2res('register.html', req, {'err': "此邮箱已被注册"})
        elif not req.POST.get('TOS'):
            return ren2res('register.html', req, {'err': "请阅读并同意用户协议"})
        else:
            pw1 = req.POST.get('Password')
            if not pw1:
                return ren2res('register.html', req, {'err': "密码不能为空"})
            pw2 = req.POST.get('Retype password')
            if pw1 != pw2:
                return ren2res('register.html', req, {'err': "密码不匹配"})
            else:
                newuser = User()
                newuser.username = email
                qq = email.replace("@qq.com", "")
                (newinfo, created) = QQUser.objects.get_or_create(user_id=qq)
                if newinfo.vcode != vcode:
                    return ren2res('register.html', req, {'err': "獭獭认证码不匹配"})
                if newinfo.vcode_time + 300 < time.time():
                    return ren2res('register.html', req, {'err': "獭獭认证码已过期"})
                newuser.set_password(pw1)
                newuser.save()
                newinfo.dbuser = newuser
                newinfo.vcode_time = 0
                newinfo.vcode = ""
                newinfo.save()
                newuser = auth.authenticate(username=email, password=pw1)
                auth.login(req, user=newuser)
                next = req.session.get('next')
                if next:
                    return HttpResponseRedirect(next)
                else:
                    return ren2res('register.html', req, {'success': "注册成功"})


@login_required(login_url='/login/')
def hunt(req):
    all_monsters = Monster.objects.all()
    all_servers = Server.objects.all()
    monster_info = {}
    hunt_list = []
    user = req.user.qquser
    TIMEFORMAT_MDHMS = "%m-%d %H:%M:%S"
    for server in all_servers:
        for monster in all_monsters:
            kill_logs = HuntLog.objects.filter(
                            hunt_group__group__member_list__contains=user.user_id,
                            monster=monster, 
                            server=server, 
                            log_type="kill")
            if not kill_logs:
                continue
            latest_kill_log = kill_logs.latest("id")
            last_kill_time = latest_kill_log.time
            global_maintain_log = HuntLog.objects.filter(server=server, log_type="maintain").latest("time")
            maintain_finish_time = global_maintain_log.time
            maintained = (maintain_finish_time > last_kill_time)
            kill_time = max(last_kill_time, maintain_finish_time)
            spawn_cooldown = (monster.first_spawn_cooldown if maintained else monster.spawn_cooldown)
            pop_cooldown = (monster.first_pop_cooldown if maintained else monster.pop_cooldown)
            next_spawn_time = kill_time + spawn_cooldown
            next_pop_time = kill_time + pop_cooldown
            cd_schedulef = spawn_cooldown / pop_cooldown
            schedulef = (time.time() - kill_time) / pop_cooldown
            cd_schedule = "{:.2%}".format(cd_schedulef)
            schedule = "{:.2%}".format(schedulef)
            if schedulef >= cd_schedulef:
                schedule_diff = schedulef - cd_schedulef
                schedule_diff = "{:.2%}".format(schedule_diff)
            else:
                schedule_diff = ""
            server_tag = server2tag(server.name)
            if next_spawn_time >= time.time():
                in_cd = "notcd"
            else:
                in_cd = ""

            monster_info["territory"] = monster.territory
            monster_info["monster"] = monster.cn_name
            monster_info["server"] = server
            monster_info["server_tag"] = server_tag
            monster_info["monster_type"] = monster.rank
            monster_info["schedule_diff"] = schedule_diff
            monster_info["cd_schedulef"] = cd_schedulef
            monster_info["cd_schedule"] = cd_schedule
            monster_info["schedulef"] = schedulef
            monster_info["schedule"] = schedule
            monster_info["in_cd"] = in_cd
            monster_info["kill_time"] = time.strftime(TIMEFORMAT_MDHMS, time.localtime(kill_time))
            monster_info["next_spawn_time"] = time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_spawn_time))
            monster_info["next_pop_time"] = time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_pop_time))
            monster_info["info"] = monster.info
            hunt_list.append(copy.deepcopy(monster_info))
    return ren2res('hunt.html', req, {"hunt_list": hunt_list})


def server2tag(server_name):
    server_tag = ""
    if server_name == "拉诺西亚":
        server_tag = "lnxy"
    elif server_name == "紫水栈桥":
        server_tag = "zszq"
    elif server_name == "幻影群岛":
        server_tag = "hyqd"
    elif server_name == "摩杜纳":
        server_tag = "mdn"
    elif server_name == "神意之地":
        server_tag = "syzd"
    elif server_name == "静语庄园":
        server_tag = "jyzy"
    elif server_name == "萌芽池":
        server_tag = "myc"
    elif server_name == "延夏":
        server_tag = "yx"
    elif server_name == "红玉海":
        server_tag = "hyh"
    elif server_name == "潮风亭":
        server_tag = "cft"
    elif server_name == "神拳痕":
        server_tag = "sqh"
    elif server_name == "白银乡":
        server_tag = "byx"
    elif server_name == "白金幻象":
        server_tag = "bjhx"
    return server_tag
