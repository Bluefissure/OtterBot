from django.http import HttpResponse, JsonResponse
from django.contrib.auth.decorators import login_required

from FFXIV import settings
from ffxivbot.models import *
from .ren2res import ren2res
import time
import json
import os
import re
import yaml
import redis
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)
REDIST_URL = "localhost" if os.environ.get('IS_DOCKER', '') != 'Docker' else 'redis'


@login_required(login_url='/login/')
def szj_auth(req):
    if req.method == "POST":
        res_dict = {"response": "No response.", "msg": "Invalid request."}
        optype = req.POST.get("optype")
        if settings.DEBUG:
            print("optype:{}".format(optype))
        if optype == "upload_uid_cookie":
            uid = req.POST.get("uid", '')
            cookie = req.POST.get("cookie", '')
            (szj_user, __) = ShizhijiaUser.objects.get_or_create(qquser=req.user.qquser)
            szj_user.user_id = uid
            szj_user.cookie = cookie
            try:
                szj_user.save()
                res_dict["response"] = "success"
            except:
                traceback.print_exc()
                res_dict["response"] = "保存失败，请联系管理员。"
            return JsonResponse(res_dict)
    return JsonResponse(res_dict)
