import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .ffxiveureka import handle_ffxiveureka
from .ffxivsc import handle_ffxivsc
from .qq import handle_qq
from .hunt import handle_hunt
from .webapi import handle_webapi

@csrf_exempt
def api(req):
    httpresponse = None
    if req.method == "POST":
        tracker = req.GET.get("tracker")
        trackers = tracker.split(",")
        if tracker:
            try:
                if "ffxiv-eureka" in trackers:
                    httpresponse = handle_ffxiveureka(req)
                if "ffxivsc" in trackers:
                    httpresponse = handle_ffxivsc(req)
                if "qq" in trackers:
                    httpresponse = handle_qq(req)
                if "hunt" in trackers:
                    httpresponse = handle_hunt(req)
                if "webapi" in trackers:
                    httpresponse = handle_webapi(req)
            except Exception as e:
                logging.error(e)
    return httpresponse or HttpResponse("Default API Error, contact dev please", status=500)



