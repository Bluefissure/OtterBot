from contextlib import redirect_stderr
import os
import time
import json

from django.contrib import auth
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from ffxivbot.models import QQUser
from authlib.integrations.requests_client import OAuth2Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)
XIVID_API_BASE = "https://api.xivid.cc/v1"

@login_required
def xivid_callback(req):
    error_msg = ""
    success_msg = ""
    try:
        with open(CONFIG_PATH, "r") as f:
            config = json.load(f)
            XIVID_CLIENT_ID = os.environ.get("XIVID_CLIENT_ID", config.get("XIVID_CLIENT_ID"))
            XIVID_KEY = os.environ.get("XIVID_KEY", config.get("XIVID_KEY"))
            WEB_BASE_URL = os.environ.get("WEB_BASE_URL", config.get("WEB_BASE_URL"))
            XIVID_RECALL_URL = os.path.join(WEB_BASE_URL, "oauth/xivid/")
        authorization_response = XIVID_RECALL_URL + '?' + req.GET.urlencode()
        print(f"authorization_response:{authorization_response}")
        scope='profile character-basic'
        client = OAuth2Session(XIVID_CLIENT_ID, XIVID_KEY, scope=scope)
        token_endpoint = XIVID_API_BASE + '/oauth/token'
        token = client.fetch_token(token_endpoint, authorization_response=authorization_response)
        user = client.get(XIVID_API_BASE + '/user').json()
        assert user['code'] == 200, "User info fetch failed"
        character = client.get(XIVID_API_BASE + '/character').json()
        assert character['code'] == 200, "Character info fetch failed"
        req.user.qquser.xivid_character = json.dumps({'data': character['data']})
        req.user.qquser.xivid_token = json.dumps(token)
        req.user.qquser.xivid_id = json.dumps(user['data']['id'])
        req.user.qquser.save()
        success_msg = "Xivid 认证成功"
    except AssertionError as e:
        error_msg = "Xivid 认证失败: " + str(e)
    except Exception as e:
        error_msg = "Xivid 认证失败"
    query_string = ""
    if error_msg or success_msg:
        query_string = "?"
        if error_msg:
            query_string += "error_msg=" + error_msg
        if success_msg:
            query_string += "success_msg=" + success_msg
    redirect_url = f"/tata{query_string}"
    return HttpResponseRedirect(redirect_url)
