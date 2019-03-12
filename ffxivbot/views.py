# -*- coding: utf-8 -*-
from django.shortcuts import render, Http404, HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.template import Context, RequestContext, loader
from django.template.context_processors import csrf
from django.http import HttpResponse
from django.http import JsonResponse
from django.db.models import Q
from django.core.files.base import ContentFile
from django.utils import timezone
from collections import OrderedDict
from django.views.decorators.csrf import csrf_exempt
import datetime
import pytz
import re
import json
import pymysql
import time
from time import strftime, localtime
from ffxivbot.models import *
from ffxivbot.webapi import webapi
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from hashlib import md5
import math
import requests
import base64
import random
import sys
import traceback
import codecs
import html
import hmac
from bs4 import BeautifulSoup
import urllib
from websocket import create_connection
import re


def ren2res(template, req, render_dict={}, post_token=True):
    render_dict.update({'user': False})
    render_dict.update(csrf(req))
    response = render(req, template, render_dict)
    return response

# Create your views here.


def tata(req):
    if req.is_ajax() and req.method == 'POST':
        res_dict = {"response": "No response."}
        optype = req.POST.get("optype")
        if (optype == "add_or_update_bot"):
            botName = req.POST.get("botName")
            botID = req.POST.get("botID")
            ownerID = req.POST.get("ownerID")
            accessToken = req.POST.get("accessToken")
            tulingToken = req.POST.get("tulingToken")
            saucenaoToken = req.POST.get("saucenaoToken")
            autoFriend = req.POST.get("autoFriend")
            autoInvite = req.POST.get("autoInvite")
            print("{},{},{},{},{},{},{}".format(botName, botID, ownerID, accessToken, tulingToken, autoFriend, autoInvite))
            if(len(botName) < 2):
                res_dict = {"response": "error", "msg": "机器人昵称太短"}
                return JsonResponse(res_dict)
            elif(len(accessToken) < 5):
                res_dict = {"response": "error", "msg": "Access Token太短"}
                return JsonResponse(res_dict)
            elif(not ownerID.strip()):
                res_dict = {"response": "error", "msg": "领养者不能为空"}
                return JsonResponse(res_dict)
            bots = QQBot.objects.filter(user_id=botID)
            if(not bots.exists()):
                bot = QQBot(user_id=botID, access_token=accessToken)
                bot_created = True
            else:
                if(bots[0].access_token != accessToken):
                    res_dict = {"response": "error", "msg": "Token错误，请确认后重试。"}
                    return JsonResponse(res_dict)
                else:
                    bot = bots[0]
                    bot_created = False
            if bot:
                bot.name = botName
                bot.owner_id = ownerID
                bot.tuling_token = tulingToken
                bot.saucenao_token = saucenaoToken
                bot.auto_accept_friend = autoFriend and "true" in autoFriend
                bot.auto_accept_invite = autoInvite and "true" in autoInvite
                if(len(QQBot.objects.all()) >= 120 and bot_created):
                    res_dict = {"response": "error", "msg": "机器人总数过多，请稍后再试"}
                    return JsonResponse(res_dict)
                bot.save()
                if(bot_created):
                    res_dict = {"response": "success", "msg": "{}({})添加成功，Token为:".format(bot.name, bot.user_id), "token": bot.access_token}
                else:
                    res_dict = {"response": "success", "msg": "{}({})更新成功，Token为:".format(bot.name, bot.user_id), "token": bot.access_token}
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
            if(optype == "switch_public"):
                bot.public = not bot.public
                bot.save()
                res_dict["response"] = "success"
            elif(optype == "del_bot"):
                bot.delete()
                res_dict["response"] = "success"
            elif(optype == "download_conf"):
                response = HttpResponse(content_type='application/octet-stream')
                response['Content-Disposition'] = 'attachment; filename="{}.json"'.format(bot.user_id)
                bot_conf = json.loads('{"host":"0.0.0.0","port":5700,"use_http":false,"ws_host":"0.0.0.0","ws_port":6700,"use_ws":false,"ws_reverse_api_url":"ws://111.231.102.248/ws_api/","ws_reverse_event_url":"ws://111.231.102.248/ws_event/","use_ws_reverse":"yes","ws_reverse_reconnect_interval":5000,"ws_reverse_reconnect_on_code_1000":"yes","post_url":"","access_token":"SECRET","secret":"","post_message_format":"string","serve_data_files":false,"update_source":"github","update_channel":"stable","auto_check_update":false,"auto_perform_update":false,"thread_pool_size":4,"server_thread_pool_size":1,"show_log_console":false,"enable_backward_compatibility":true}')
                bot_conf["secret"] = bot.access_token
                response.write(json.dumps(bot_conf, indent=4))
                return response
            print(optype)
            print(req.POST)
        return JsonResponse(res_dict)

    bots = QQBot.objects.all()
    bot_list = []
    for bot in bots:
        bb = {}
        version_info = json.loads(bot.version_info)
        coolq_edition = version_info["coolq_edition"] if version_info and "coolq_edition" in version_info.keys() else ""
        if coolq_edition != "":
            coolq_edition = coolq_edition[0].upper() + coolq_edition[1:]
        friend_list = json.loads(bot.friend_list)
        friend_num = len(friend_list["friends"]) if friend_list and "friends" in friend_list.keys() else "-1"
        group_list = json.loads(bot.group_list)
        group_num = len(group_list)
        bb["name"] = bot.name
        if bot.public:
            bb["user_id"] = bot.user_id
        else:
            mid = len(bot.user_id) // 2
            user_id = bot.user_id[:mid - 2] + "*" * 4 + bot.user_id[mid + 2:]
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
    return ren2res("pages/tables/data.html", req, {"bots": bot_list})


def quest(req):
    if req.is_ajax() and req.method == 'POST':
        res_dict = {"response": "No response."}
        optype = req.POST.get("optype")
        if(optype == "search_quest"):
            max_iter = req.POST.get("max_iter")
            main_quest = req.POST.get("main_quest")
            main_quest = main_quest and "true" in main_quest
            sub_quest = req.POST.get("sub_quest")
            sub_quest = sub_quest and "true" in sub_quest
            start_quest = req.POST.get("start_quest")
            start_quest = PlotQuest.objects.filter(name=start_quest)
            start_quest = start_quest[0] if start_quest else None
            end_quest = req.POST.get("end_quest")
            end_quest = PlotQuest.objects.filter(name=end_quest)
            end_quest = end_quest[0] if end_quest else None
            max_iter = req.POST.get("max_iter")
            print("main_quest:{}".format(main_quest))
            print("sub_quest:{}".format(sub_quest))
            quest_dict = {}
            tmp_edge_list = []
            edge_list = []
            if(not start_quest and not end_quest):
                res_dict["response"] = "找不到对应任务"
            elif(start_quest and end_quest):
                res_dict["response"] = "TODO: Double Quest Search"
            else:
                single_quest = start_quest or end_quest
                search_list = []
                search_iter = 0
                search_list.append((single_quest, 1, 1))
                search_list.append((single_quest, 2, 1))
                if ("主线" in single_quest.category and not main_quest) or (not "主线" in single_quest.category and not sub_quest):
                    res_dict["response"] = "查询任务类别与所选类别不符，清选择正确的类别。"
                    return JsonResponse(res_dict)
                done_cnt = 0
                tot_cnt = 0
                while(search_list and search_iter <= min(int(max_iter), 1000)):
                    try:
                        (now_quest, direction, search_iter) = search_list[0]
                        search_list = search_list[1:]
                        if "主线" in now_quest.category:
                            if(not main_quest):
                                continue
                        elif not sub_quest:
                            continue
                        if(direction == 2):
                            done_cnt += 1
                        now_quest_dict = {
                            "description": now_quest.category,
                            "startnpc": now_quest.startnpc,
                            "endnpc": now_quest.endnpc,
                        }
                        if now_quest.name not in quest_dict.keys():
                            quest_dict[now_quest.name] = now_quest_dict
                        else:
                            if(now_quest.name != single_quest.name):
                                continue
                        if not now_quest.endpoint:
                            if direction == 1:
                                for quest in now_quest.suf_quests.all():
                                    if(quest.name not in quest_dict.keys()):
                                        search_list.append((quest, 1, search_iter + 1))
                                    edge = {"from": now_quest.name, "to": quest.name, }
                                    if edge not in edge_list:
                                        tmp_edge_list.append(edge)
                        if not now_quest.endpoint or (now_quest.endpoint and now_quest.name == single_quest.name):
                            if direction == 2:
                                for quest in now_quest.pre_quests.all():
                                    if(quest.name not in quest_dict.keys()):
                                        search_list.append((quest, 2, search_iter + 1))
                                    edge = {"from": quest.name, "to": now_quest.name, }
                                    if edge not in edge_list:
                                        tmp_edge_list.append(edge)
                    except Exception as e:
                        print(e)
                for edge in tmp_edge_list:
                    if edge["from"] in quest_dict.keys() and edge["to"] in quest_dict.keys():
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


def get_nm_id(tracker, nm_name):
    if(tracker == "ffxiv-eureka"):
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
            "娄希": 37
        }
        for (k, v) in name_id.items():
            if(k in nm_name):
                return v
    if(tracker == "ffxivsc"):
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
            "娄希": {"level": 36, "type": 2}
        }
        for (k, v) in name_id.items():
            if(k in nm_name):
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
    if(len(segs) < 3):
        return msg
    map_name = segs[0].strip()
    map_pos = segs[1].strip()
    ts = Territory.objects.filter(name__icontains=map_name.strip())
    if(ts.exists()):
        t = ts[0]
        x, y = map(float, map_pos.replace("(", "").replace(")", "").split(","))
        new_msg += "\nMap:https://map.wakingsands.com/#f=mark&x={}&y={}&id={}".format(x, y, t.mapid)
    print(new_msg)
    return new_msg


@csrf_exempt
def api(req):
    httpresponse = None
    if req.method == "POST":
        tracker = req.GET.get('tracker')
        trackers = tracker.split(',')
        print("tracker:{}".format(tracker))
        if(tracker):
            if("ffxiv-eureka" in trackers):
                instance = req.GET.get('instance')
                password = req.GET.get('password')
                # print("ffxiv-eureka {}:{}".format(instance,password))
                if(instance and password):
                    nm_name = req.POST.get('text')

                    if(nm_name):
                        nm_id = get_nm_id("ffxiv-eureka", nm_name)
                        # print("nm_name:{} id:{}".format(nm_name,nm_id))
                        if(nm_id > 0):
                            # print("nm_name:{} nm_id:{}".format(nm_name,nm_id))
                            # ws = create_connection("wss://ffxiv-eureka.com/socket/websocket?vsn=2.0.0")
                            ws = create_connection("wss://eureka.bluefissure.com/socket/websocket?vsn=2.0.0")
                            msg = '["1","1","instance:{}","phx_join",{{"password":"{}"}}]'.format(instance, password)
                            # print(msg)
                            ws.send(msg)
                            msg = '["1","2","instance:{}","set_kill_time",{{"id":{},"time":{}}}]'.format(instance, nm_id, int(time.time() * 1000))
                            # print(msg)
                            ws.send(msg)
                            ws.close()
                            httpresponse = HttpResponse("OK", status=200)
                    else:
                        print("no nm_name")
            if("ffxivsc" in trackers):
                key = req.GET.get('key')
                # print("ffxiv-eureka {}:{}".format(instance,password))
                if(key):
                    nm_name = req.POST.get('text')
                    if(nm_name):
                        nm_level_type = get_nm_id("ffxivsc", nm_name)
                        if(int(nm_level_type["type"]) > 0):
                            url = 'https://api.ffxivsc.cn/EurekaService/lobby/addKillTime'
                            post_data = {
                                "killTime": strftime('%Y-%m-%d %H:%M', time.localtime()),
                                "level": "{}".format(nm_level_type["level"]),
                                "key": key,
                                "type": "{}".format(nm_level_type["type"])
                                }
                            r = requests.post(url=url, data=post_data)
                            httpresponse = HttpResponse(r)
                    else:
                        print("no nm_name")
            if("qq" in trackers):
                bot_qq = req.GET.get('bot_qq')
                qq = req.GET.get('qq')
                token = req.GET.get('token')
                group_id = req.GET.get('group')
                print("bot: {} qq:{} token:{}".format(bot_qq, qq, token))
                if(bot_qq and qq and token):
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
                        if (time.time() < qquser.last_api_time + qquser.api_interval):
                            api_rate_limit = False
                            print("qquser {} api rate limit exceed".format(qq))
                        qquser.last_api_time = int(time.time())
                        qquser.save(update_fields=["last_api_time"])
                    except QQUser.DoesNotExist:
                        print("qquser {}:{} auth fail".format(qq, token))
                        qquser = None
                    if bot and qquser and api_rate_limit:
                        channel_layer = get_channel_layer()
                        msg = req.POST.get('text')
                        reqbody = req.body
                        try:
                            if reqbody:
                                reqbody = reqbody.decode()
                                reqbody = json.loads(reqbody)
                                msg = msg or reqbody["content"]
                                msg = re.compile('[\\x00-\\x08\\x0b-\\x0c\\x0e-\\x1f]').sub(' ', msg)
                        except BaseException:
                            pass
                        print("body:{}".format(req.body.decode()))
                        if group_id:
                            try:
                                group = QQGroup.objects.get(group_id=group_id)
                                group_push_list = [user["user_id"] for user in json.loads(group.member_list) if (user["role"] == "owner" or user["role"] == "admin")]
                                print("group push list:{}".format(group_push_list))
                            except QQGroup.DoesNotExist:
                                print("group:{} does not exist".format(group_id))
                        print(group and group.api and int(qquser.user_id) in group_push_list)
                        msg = handle_hunt_msg(msg)
                        if group and group.api and int(qquser.user_id) in group_push_list:
                            jdata = {
                                "action": "send_group_msg",
                                "params": {"group_id": group.group_id, "message": "Message from [CQ:at,qq={}]:\n{}".format(qquser.user_id, msg)},
                                "echo": "",
                            }
                        else:
                            jdata = {
                                "action": "send_private_msg",
                                "params": {"user_id": qquser.user_id, "message": msg},
                                "echo": "",
                            }
                        async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event", "text": json.dumps(jdata), })
                        httpresponse = HttpResponse("OK", status=200)
            if("webapi" in trackers):
                qq = req.GET.get('qq')
                token = req.GET.get('token')
                print("qq:{}\ntoken:{}".format(qq, token))
                if(qq and token):
                    qquser = None
                    try:
                        qquser = QQUser.objects.get(user_id=qq, bot_token=token)
                    except QQUser.DoesNotExist:
                        res_dict = {"response": "error", "msg": "Invalid API token", "rcode": "101"}
                        return JsonResponse(res_dict)
                    if qquser:
                        res_dict = webapi(req)
                        return JsonResponse(res_dict)
                else:
                    res_dict = {"response": "error", "msg": "Invalid request", "rcode": "100"}
                    return JsonResponse(res_dict)
                return HttpResponse(status=500)
    return httpresponse if httpresponse else HttpResponse(status=404)


@csrf_exempt
def qqpost(req):
    pass
