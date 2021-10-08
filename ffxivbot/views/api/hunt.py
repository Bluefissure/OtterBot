import os
import re
import time
import json
import redis
import hashlib
import logging
import requests
from asgiref.sync import async_to_sync
from django.http import HttpResponse
from channels.layers import get_channel_layer
from ffxivbot.models import QQBot, QQUser, HuntGroup, Monster, Server, HuntLog


def handle_hunt(req):
    qq = req.GET.get("qq")
    token = req.GET.get("token")
    group_id = req.GET.get("group")
    bot_qq = req.GET.get("bot_qq")
    if not (bot_qq and qq and token):
        return HttpResponse("Missing URL parameters", status=500)
    qquser = None
    group = None
    try:
        bot = QQBot.objects.get(user_id=bot_qq)
        qquser = QQUser.objects.get(user_id=qq)
        if qquser.bot_token != token:
            return HttpResponse("Wrong bot token {}".format(token), status=403)
    except QQUser.DoesNotExist:
        return HttpResponse("QQuser {} does not exist".format(qq, token), status=404)
    except QQBot.DoesNotExist:
        return HttpResponse("Bot {} does not exist".format(bot_qq), status=404)
    else:
        channel_layer = get_channel_layer()
        reqbody = json.loads(req.body.decode())
        try:
            hunt_group = HuntGroup.objects.get(
                group__group_id=group_id
            )
            group = hunt_group.group
            group_push_list = [
                user["user_id"]
                for user in json.loads(group.member_list)
            ]
            if not int(qquser.user_id) in group_push_list:
                return HttpResponse("You're not in the group member list", status=403)
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
                if str(monster.territory) != zone_name:  # "ZoneName2"
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
                logging.info(
                    "Get HuntLog info:\nmonster:{}\nserver:{}".format(monster, server)
                )

                r = redis.Redis(host="localhost", port=6379, decode_responses=True)
                hunt_log_hash = hashlib.md5(
                    "hunt_log|{}|{}|{}|{}".format(
                        monster,
                        server,
                        hunt_group.group.group_id,
                        "kill"
                    ).encode()).hexdigest()
            
                if r.get(hunt_log_hash):
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
                    r.set(hunt_log_hash, time.time(), ex=60)
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
                        return HttpResponse(r)
            return HttpResponse(status=200)
        except HuntGroup.DoesNotExist:
            return HttpResponse(
                "HuntGroup:{} does not exist".format(group_id),
                status=404,
            )
        except Monster.DoesNotExist:
            return HttpResponse(
                "Monster:{} does not exist".format(monster_name),
                status=404,
            )
        except Server.DoesNotExist:
            return HttpResponse(
                "Server:{} does not exist".format(world_name),
                status=404,
            )