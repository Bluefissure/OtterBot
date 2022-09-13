import json
import time
import os
import logging
import requests
from urllib.parse import unquote
from django.http import HttpResponse
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from ffxivbot.models import QQBot, QQGroup, CommandLog


def generate_msg(heartbeat, monitor):
    name = monitor.get("name", "unknown")
    url = monitor.get("url", "unknown")
    time = heartbeat.get("time", "unknown")
    error = heartbeat.get("msg", "unknown")
    msg = ""
    if heartbeat.get("status", -1) == 0:
        msg = f"""
❌ Your service {name} went down. ❌
Service Name:
{name}
Service URL:
{url}
Time (UTC):
{time}
Error:
{error}"""
    elif heartbeat.get("status", -1) == 1:
        ping = heartbeat.get("ping", 0)
        msg = f"""
✅ Your service {name} is up. ✅
Service Name:
{name}
Service URL:
{url}
Time (UTC):
{time}
Ping:
{ping}ms"""
    return msg

def handle_uptime_kuma(req):
    # Bot check & group check
    bot_qq = req.GET.get("bot_qq")
    group_id = req.GET.get("group")
    access_token = unquote(req.GET.get("access_token", ""))
    try:
        bot = QQBot.objects.get(user_id=bot_qq)
    except QQBot.DoesNotExist:
        return HttpResponse("Bot {} does not exist".format(bot_qq), status=404)
    if not bot.api:
        return HttpResponse("API for bot {} is disabled".format(bot_qq), status=403)
    if bot.access_token != access_token:
        return HttpResponse("Access token is incorrect.".format(bot_qq), status=401)
    try:
        group = QQGroup.objects.get(group_id=group_id)
    except QQGroup.DoesNotExist:
        return HttpResponse("Group {} does not exist".format(group_id), status=404)
    
    req_json = json.loads(req.body)
    heartbeat = req_json.get("heartbeat", {})
    monitor = req_json.get("monitor", {})
    req_msg = req_json.get("msg", "")
    msg = ""
    if req_msg.endswith("Testing"):
        msg = req_msg
    else:
        if not monitor:
            return HttpResponse("No monitor", status=400)
        if not heartbeat:
            return HttpResponse("No heartbeat", status=400)
        if not heartbeat.get("important", False):
            return HttpResponse("Not important", status=200)
        msg = generate_msg(heartbeat, monitor)
    msg = msg.strip()
    if msg:
        channel_layer = get_channel_layer()
        jdata = {
            "action": "send_group_msg",
            "params": {
                "group_id": group.group_id,
                "message": msg,
            },
            "echo": "",
        }
        log = CommandLog(
            time=time.time(),
            command="api:uptime_kuma",
            message=json.dumps(jdata),
            bot_id=bot.user_id,
            user_id=bot.owner_id,
            group_id=group.group_id,
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

