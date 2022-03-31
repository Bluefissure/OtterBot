
import re
import json
import hashlib
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from ffxivbot.models import QQBot, QQGroup


@csrf_exempt
def dalamud_feedback(req):
    base_api_regex = r"^\/dalamud\/feedback\/"
    if req.method == "POST":
        channel_layer = get_channel_layer()
        req_j = json.loads(req.body)
        try:
            group = QQGroup.objects.get(group_id='827725124')
            bot = QQBot.objects.filter(owner_id='306401806')[0]
        except:
            return HttpResponse("Server Error", status=500)
        msg = "收到来自 {} 关于 {}(v{}) 的反馈如下：\n{}".format(
            req_j.get('reporter', ''),
            req_j.get('name', ''),
            req_j.get('version', '0.0.0.0'),
            req_j.get('content', '')
        ) 
        jdata = {
            "action": "send_group_msg",
            "params": {
                "group_id": group.group_id,
                "message": msg,
            },
            "echo": "",
        }
        async_to_sync(channel_layer.send)(
            bot.api_channel_name,
            {"type": "send.event", "text": json.dumps(jdata)},
        )
        print("====== dalamud_feedback POST ======")
        print(msg)
        print("====== dalamud_feedback END  ======")
    elif req.method == "GET":
        return HttpResponse("Method not allowed", status=405)
    return HttpResponse("Default API Error, contact dev please.", status=500)
