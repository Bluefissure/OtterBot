import os
import re
import time
import json
import logging
import requests
from asgiref.sync import async_to_sync
from django.http import HttpResponse
from channels.layers import get_channel_layer
from ffxivbot.models import QQBot, QQUser, QQGroup, Territory, CommandLog
from .webapi import github_webhook
from .matcha import get_matcha_fate_name


def handle_qq(req):
    bot_qq = req.GET.get("bot_qq")
    qq = req.GET.get("qq")
    token = req.GET.get("token")
    group_id = req.GET.get("group")
    if not (bot_qq and qq and token):
        return None
    bot = None
    qquser = None
    group = None
    try:
        bot = QQBot.objects.get(user_id=bot_qq)
    except QQBot.DoesNotExist:
        return HttpResponse("Bot {} does not exist".format(bot_qq), status=404)
    if not bot.api:
        return HttpResponse(
            "API for bot {} is disabled".format(bot_qq), status=401
        )
    try:
        qquser = QQUser.objects.get(user_id=qq)
        if qquser.bot_token != token:
            return HttpResponse(
                "QQUser {}:{} auth fail".format(qq, token), status=401
            )
    except QQUser.DoesNotExist:
        return HttpResponse(
            "QQUser {} does not exist".format(qq), status=404
        )

    time_diff = qquser.last_api_time + qquser.api_interval - time.time()
    if time_diff > 0:
        return HttpResponse(
            "QQUser {}: rate limit exceeded, next in {} seconds".format(
                qq, time_diff
            ), status=429
        )
    qquser.last_api_time = int(time.time())
    qquser.save(update_fields=["last_api_time"])

    channel_layer = get_channel_layer()
    msg = get_msg_from_req(req)
    try:
        msg = msg or github_webhook(req)
        msg = msg or get_matcha_fate_name(req)
    except BaseException:
        pass
    if not msg:
        return HttpResponse("Can't get message", status=400)
    else:
        if group_id:
            try:
                group = QQGroup.objects.get(group_id=group_id)
                group_push_list = [
                    user["user_id"]
                    for user in json.loads(group.member_list)
                    if (user["role"] in ("owner", "admin"))
                ]
            except QQGroup.DoesNotExist:
                return HttpResponse("Group {} does not exist".format(group_id), status=404)
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
                    "message": "Message from {}:\n{}".format(at_msg, msg),
                },
                "echo": "",
            }
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
                return HttpResponse(r)
        return HttpResponse("OK", status=200)


def get_msg_from_req(req):
    msg = req.POST.get("text")
    reqbody = req.body
    try:
        if reqbody:
            reqbody = reqbody.decode()
            reqjson = json.loads(reqbody)
            if isinstance(reqjson, dict):
                msg = msg or reqjson.get("content")
            elif isinstance(reqjson, list):
                msg_list = reqjson
                msg = ""
                for msg_block in msg_list:
                    if msg_block["type"] == "text":
                        msg += msg_block["data"]["text"]
                    elif msg_block["type"] == "image":
                        msg += "[CQ:image,file={}]".format(msg_block["data"]["file"])
                    elif msg_block["type"] == "face":
                        msg += "[CQ:face,id={}]".format(msg_block["data"]["id"])
            msg = re.compile(
                "[\\x00-\\x08\\x0b-\\x0c\\x0e-\\x1f]"
            ).sub(" ", msg)
    except BaseException:
        pass
    return msg

def handle_hunt_msg(msg):
    if msg.find("hunt") != 0:
        return msg
    new_msg = msg.replace("hunt", "", 1)
    segs = new_msg.split("|")
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
    return new_msg
