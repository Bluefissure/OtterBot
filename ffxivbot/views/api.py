import logging
import os
import re
import requests

from time import strftime

from asgiref.sync import async_to_sync
from django.http import HttpResponse, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction
from channels.layers import get_channel_layer
from ffxivbot.models import *
from ffxivbot.webapi import github_webhook, webapi
from websocket import create_connection


def get_matcha_nm_name(req):
    nm_name = ""
    try:
        matcha_json = json.loads(req.body)
        if matcha_json.get("event") == "Fate":
            incoming_data = matcha_json.get("data")
            event_type = incoming_data.get("type")
            if event_type == "start":
                fate_id = incoming_data.get("fate")
                nm_name = nm_id2name(fate_id)
            else:
                print("Won't handle fate event other than 'start'.")
    except JSONDecodeError:
        pass
    return nm_name


def get_matcha_fate_name(req):
    fate_name = ""
    try:
        matcha_json = json.loads(req.body)
        if matcha_json.get("event") == "Fate":
            incoming_data = matcha_json.get("data")
            event_type = incoming_data.get("type")
            if event_type == "start":
                fate_id = incoming_data.get("fate")
                fate_name = fate_id2name(fate_id)
            else:
                print("Won't handle fate event other than 'start'.")
    except JSONDecodeError:
        pass
    return fate_name


@csrf_exempt
def api(req):
    httpresponse = None
    if req.method == "POST":
        print("GET:{}".format(req.GET))
        tracker = req.GET.get("tracker")
        print("tracker:{}".format(tracker))
        trackers = tracker.split(",")
        if tracker:
            if "ffxiv-eureka" in trackers:
                instance = req.GET.get("instance")
                password = req.GET.get("password")
                # print("ffxiv-eureka {}:{}".format(instance, password))
                if instance and password:
                    nm_name = req.POST.get("text")
                    if not nm_name:
                        nm_name = get_matcha_nm_name(req)
                    if nm_name:
                        nm_id = get_nm_id("ffxiv-eureka", nm_name)
                        # print("nm_name:{} id:{}".format(nm_name, nm_id))
                        if nm_id > 0:
                            # print("nm_name:{} nm_id:{}".format(nm_name, nm_id))
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
                        return HttpResponse("No NM name provided", status=500)
            if "ffxivsc" in trackers:
                key = req.GET.get("key")
                if key:
                    nm_name = req.POST.get("text")
                    if not nm_name:
                        nm_name = get_matcha_nm_name(req)
                    if nm_name:
                        nm_level_type = get_nm_id("ffxivsc", nm_name)
                        if int(nm_level_type["type"]) > 0:
                            url = "https://api.ffxivsc.cn/ffxivsc_eureka_v3-3.0/lobby/addKillTime"
                            post_data = {
                                "level": "{}".format(nm_level_type["level"]),
                                "key": key,
                                "type": "{}".format(nm_level_type["type"]),
                            }
                            r = requests.post(url=url, data=post_data)
                            httpresponse = HttpResponse(r)
                        else:
                            return HttpResponse(
                                "No nm_level_type can be found", status=500
                            )
                    else:
                        print("no nm_name")
                        return HttpResponse("No NM name provided", status=500)
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
                    except QQBot.DoesNotExist as e:
                        print("Bot {} does not exist".format(bot_qq))
                    if bot and not bot.api:
                        print("API for bot {} is disabled".format(bot_qq))
                        httpresponse = HttpResponse(
                            "API for bot {} is disabled".format(bot_qq), status=500
                        )
                    try:
                        qquser = QQUser.objects.get(user_id=qq, bot_token=token)
                        if time.time() < qquser.last_api_time + qquser.api_interval:
                            api_rate_limit = False
                            print("qquser {} api rate limit exceed".format(qq))
                        qquser.last_api_time = int(time.time())
                        qquser.save(update_fields=["last_api_time"])
                    except QQUser.DoesNotExist:
                        print("qquser {}:{} auth fail".format(qq, token))
                        httpresponse = HttpResponse(
                            "QQUser {}:{} auth fail".format(qq, token), status=500
                        )

                    if bot and bot.api and qquser and api_rate_limit:
                        channel_layer = get_channel_layer()
                        msg = req.POST.get("text")
                        reqbody = req.body
                        # print("reqbody:{}".format(reqbody))
                        try:
                            if reqbody:
                                reqbody = reqbody.decode()
                                # print("reqbody1:{}".format(reqbody))
                                reqbody = json.loads(reqbody)
                                # print("reqbody2:{}".format(reqbody))
                                msg = msg or reqbody.get("content")
                                msg = re.compile(
                                    "[\\x00-\\x08\\x0b-\\x0c\\x0e-\\x1f]"
                                ).sub(" ", msg)
                        except BaseException:
                            pass
                        if not msg:
                            try:
                                msg = github_webhook(req)
                            except BaseException:
                                pass
                        if not msg:
                            try:
                                msg = get_matcha_fate_name(req)
                            except BaseException:
                                pass
                        if not msg:
                            print(
                                "Can't get msg from request:{}:{}".format(req, reqbody)
                            )
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
                                at_msg = (
                                    "[CQ:at,qq={}]".format(qquser.user_id)
                                    if req.GET.get("at", "true") == "true"
                                    else str(qquser.user_id)
                                )
                                jdata = {
                                    "action": "send_group_msg",
                                    "params": {
                                        "group_id": group.group_id,
                                        "message": "Message from {}:\n{}".format(
                                            at_msg, msg
                                        ),
                                    },
                                    "echo": "",
                                }
                                log = CommandLog(
                                    time=time.time(),
                                    command="api:qq",
                                    message=json.dumps(jdata),
                                    bot_id=bot.user_id,
                                    user_id=qquser.user_id,
                                    group_id=group.group_id
                                )
                                log.save()
                            else:
                                jdata = {
                                    "action": "send_private_msg",
                                    "params": {
                                        "user_id": qquser.user_id,
                                        "message": msg,
                                    },
                                    "echo": "",
                                }
                                log = CommandLog(
                                    time=time.time(),
                                    command="api:qq",
                                    message=json.dumps(jdata),
                                    bot_id=bot.user_id,
                                    user_id=qquser.user_id,
                                    group_id=""
                                )
                                log.save()
                            if not bot.api_post_url:
                                async_to_sync(channel_layer.send)(
                                    bot.api_channel_name,
                                    {"type": "send.event", "text": json.dumps(jdata)},
                                )
                            else:
                                url = os.path.join(
                                    bot.api_post_url,
                                    "{}?access_token={}".format(
                                        jdata["action"], bot.access_token
                                    ),
                                )
                                headers = {"Content-Type": "application/json"}
                                r = requests.post(
                                    url=url,
                                    headers=headers,
                                    data=json.dumps(jdata["params"]),
                                )
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
                        httpresponse = HttpResponse(
                            "User API rate limit exceed", status=500
                        )
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
                                hunt_group = HuntGroup.objects.get(
                                    group__group_id=group_id
                                )
                                group = hunt_group.group
                                group_push_list = [
                                    user["user_id"]
                                    for user in json.loads(group.member_list)
                                ]
                                assert (
                                    int(qquser.user_id) in group_push_list
                                ), "You're not in the group member list"
                                monster_name = reqbody["monster"]
                                zone_name = reqbody["zone"]
                                zone_name = (
                                    zone_name.replace(chr(57521), "")
                                    .replace(chr(57522), "2")
                                    .replace(chr(57523), "3")
                                )
                                try:
                                    monster = Monster.objects.get(cn_name=monster_name)
                                except Monster.DoesNotExist:
                                    monster = Monster.objects.get(
                                        cn_name=re.sub("1|2|3", "", monster_name)
                                    )
                                world_name = reqbody.get("world", "None")
                                timestamp = int(reqbody["time"])
                                server = None
                                world_id = reqbody.get("worldid", -1)
                                servers = Server.objects.filter(worldId=world_id)
                                server = (
                                    servers[0]
                                    if servers.exists()
                                    else Server.objects.get(name=world_name)
                                )
                                success = False
                                # handle instances
                                if (
                                    req.GET.get("strict_zone", "true") == "false"
                                    or str(monster.territory) in zone_name
                                ):  # "ZoneName2", "ZoneName"
                                    if (
                                        str(monster.territory) != zone_name
                                    ):  # "ZoneName2"
                                        monster_name = zone_name.replace(
                                            str(monster.territory), monster_name
                                        )  # "ZoneName2" -> "MonsterName2"
                                        try:
                                            monster = Monster.objects.get(
                                                cn_name=monster_name
                                            )
                                        except Monster.DoesNotExist:
                                            monster = Monster.objects.get(
                                                cn_name=re.sub(
                                                    "1|2|3", "", monster_name
                                                )
                                            )
                                    print(
                                        "Get HuntLog info:\nmonster:{}\nserver:{}".format(
                                            monster, server
                                        )
                                    )
                                    
                                    with transaction.atomic():
                                        if HuntLog.objects.filter(
                                            monster=monster,
                                            server=server,
                                            hunt_group=hunt_group,
                                            log_type="kill",
                                            time__gt=timestamp - 60,
                                        ).exists():
                                            msg = '{}——"{}" 已在一分钟内记录上报，此次API调用被忽略'.format(
                                                server,
                                                monster,
                                                time.strftime(
                                                    "%Y-%m-%d %H:%M:%S",
                                                    time.localtime(timestamp),
                                                ),
                                            )
                                            success = False
                                        else:
                                            hunt_log = HuntLog(
                                                monster=monster,
                                                hunt_group=hunt_group,
                                                server=server,
                                                log_type="kill",
                                                time=timestamp,
                                            )
                                            hunt_log.save()
                                            msg = '{}——"{}" 击杀时间: {}'.format(
                                                hunt_log.server,
                                                monster,
                                                time.strftime(
                                                    "%Y-%m-%d %H:%M:%S",
                                                    time.localtime(timestamp),
                                                ),
                                            )
                                            at_msg = (
                                                "[CQ:at,qq={}]".format(qquser.user_id)
                                                if req.GET.get("at", "true") == "true"
                                                else str(qquser.user_id)
                                            )
                                            msg = at_msg + "通过API更新了如下HuntLog:\n{}".format(
                                                msg
                                            )
                                            success = True
                                else:
                                    at_msg = (
                                        "[CQ:at,qq={}]".format(qquser.user_id)
                                        if req.GET.get("at", "true") == "true"
                                        else str(qquser.user_id)
                                    )
                                    msg = at_msg + "上报 {} 失败，{} 与 {} 不兼容".format(
                                        monster, monster.territory, zone_name
                                    )
                                    success = False
                                if success or req.GET.get("verbose", "false") == "true":
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
                                            {
                                                "type": "send.event",
                                                "text": json.dumps(jdata),
                                            },
                                        )
                                    else:
                                        url = os.path.join(
                                            bot.api_post_url,
                                            "{}?access_token={}".format(
                                                jdata["action"], bot.access_token
                                            ),
                                        )
                                        headers = {"Content-Type": "application/json"}
                                        r = requests.post(
                                            url=url,
                                            headers=headers,
                                            data=json.dumps(jdata["params"]),
                                        )
                                        if r.status_code != 200:
                                            logging.error(r.text)
                                httpresponse = HttpResponse(status=200)
                            except HuntGroup.DoesNotExist:
                                print("HuntGroup:{} does not exist".format(group_id))
                                httpresponse = HttpResponse(
                                    "HuntGroup:{} does not exist".format(group_id),
                                    status=500,
                                )
                            except Monster.DoesNotExist:
                                print("Monster:{} does not exist".format(monster_name))
                                httpresponse = HttpResponse(
                                    "Monster:{} does not exist".format(monster_name),
                                    status=500,
                                )
                            except Server.DoesNotExist:
                                print("Server:{} does not exist".format(world_name))
                                httpresponse = HttpResponse(
                                    "Server:{} does not exist".format(world_name),
                                    status=500,
                                )
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
    return (
        httpresponse
        if httpresponse
        else HttpResponse("Default API Error, contact dev please.", status=500)
    )


def fate_id2name(fate_id):
    r = requests.get(
        "http://cafemaker.wakingsands.com/Fate/{}".format(fate_id), timeout=3
    )
    j = r.json()
    return j.get("Name")


def nm_id2name(fate_id):
    map_id2name = {
        1328: "常风皇帝",
        1329: "帕祖祖",
        1331: "法夫纳",
        1332: "科里多仙人刺",
        1333: "忒勒斯",
        1334: "阿米特",
        1335: "盖因",
        1336: "庞巴德",
        1337: "波吕斐摩斯",
        1338: "拉玛什图",
        1339: "塞尔凯特",
        1340: "阿玛洛克",
        1341: "极其危险物质",
        1342: "阔步西牟鸟",
        1343: "白骑士",
        1344: "卡利斯托",
        1345: "哲罕南",
        1346: "武断魔花茱莉卡",
        1347: "群偶",
        1348: "常风领主",
        1351: "雪之女王",
        1352: "苏罗毗",
        1353: "灰烬龙",
        1354: "异形魔虫",
        1355: "安娜波",
        1356: "阿萨格",
        1357: "雪屋王",
        1358: "唇亡齿寒",
        1359: "荷鲁斯",
        1360: "亚瑟罗王",
        1361: "优雷卡圣牛",
        1362: "哈达约什",
        1363: "总领安哥拉·曼纽",
        1364: "娄希",
        1365: "复制魔花凯西",
        1366: "白泽",
        1369: "塔克西姆",
        1370: "贝南德纳出现",
        1388: "琉科西亚",
        1389: "佛劳洛斯",
        1390: "诡辩者",
        1391: "格拉菲亚卡内",
        1392: "阿斯卡拉福斯",
        1393: "巴钦大公爵",
        1394: "埃托洛斯",
        1395: "来萨特",
        1396: "火巨人",
        1397: "伊丽丝",
        1398: "佣兵雷姆普里克斯",
        1399: "闪电督军",
        1400: "樵夫杰科",
        1401: "明眸",
        1402: "阴·阳",
        1403: "斯库尔",
        1404: "彭忒西勒亚",
        1412: "卡拉墨鱼",
        1413: "剑齿象",
        1414: "摩洛",
        1415: "皮艾萨邪鸟",
        1416: "霜鬃猎魔",
        1417: "达佛涅",
        1418: "戈尔德马尔王",
        1419: "琉刻",
        1420: "巴龙",
        1421: "刻托",
        1423: "起源守望者",
    }
    return "" if fate_id not in map_id2name else map_id2name[fate_id]


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
