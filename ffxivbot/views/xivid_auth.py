import os
import json
from django.http import HttpResponseRedirect
from django.contrib.auth.decorators import login_required

from authlib.integrations.requests_client import OAuth2Session

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)

@login_required
def xivid_auth(req):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        XIVID_CLIENT_ID = os.environ.get("XIVID_CLIENT_ID", config.get("XIVID_CLIENT_ID"))
        XIVID_KEY = os.environ.get("XIVID_KEY", config.get("XIVID_KEY"))
    scope='profile character-basic'
    client = OAuth2Session(XIVID_CLIENT_ID, XIVID_KEY, scope=scope)
    authorization_endpoint = 'https://api.xivid.cc/v1/oauth/authorize'
    uri, state = client.create_authorization_url(authorization_endpoint)
    req.user.qquser.xivid_state = state
    req.user.qquser.save()
    return HttpResponseRedirect(uri)
