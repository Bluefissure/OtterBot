import requests
from django.http import HttpResponse
from .matcha import get_matcha_nm_name, get_matcha_fate_name
from .utils import get_nm_id


def handle_ffxivsc(req):
    key = req.GET.get("key")
    if not key:
        return None
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
            r = requests.post(url=url, data=post_data, timeout=30)
            return HttpResponse(r)
        else:
            return HttpResponse(
                "No nm_level_type can be found", status=500
            )
    else:
        return HttpResponse("No NM name provided", status=500)