import time
from websocket import create_connection
from django.http import HttpResponse
from .matcha import get_matcha_nm_name, get_matcha_fate_name
from .utils import get_nm_id

def handle_ffxiveureka(req):
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
                return HttpResponse("OK", status=200)
        else:
            # print("no nm_name")
            return HttpResponse("No NM name provided", status=500)