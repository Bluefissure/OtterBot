import logging
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from .ffxiveureka import handle_ffxiveureka
from .ffxivsc import handle_ffxivsc
from .qq import handle_qq
from .hunt import handle_hunt
from .webapi import handle_webapi
from .uptime_kuma import handle_uptime_kuma

@csrf_exempt
def api(req):
    httpresponse = None
    if req.method == "POST":
        tracker = req.GET.get("tracker")
        print(tracker)
        trackers = tracker.split(",")
        print(trackers)
        if tracker:
            try:
                if "ffxiv-eureka" in trackers:
                    httpresponse = handle_ffxiveureka(req)
                elif "ffxivsc" in trackers:
                    httpresponse = handle_ffxivsc(req)
                elif "qq" in trackers:
                    httpresponse = handle_qq(req)
                elif "hunt" in trackers:
                    httpresponse = handle_hunt(req)
                elif "webapi" in trackers:
                    httpresponse = handle_webapi(req)
                elif "uptime-kuma" in trackers:
                    print("kuma")
                    httpresponse = handle_uptime_kuma(req)
            except Exception as e:
                logging.error(e)
    return httpresponse or HttpResponse("Default API Error, contact dev please", status=500)



