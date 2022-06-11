import os
import json
from django.http import HttpResponseRedirect

from ffxivbot.oauth_client import OAuthQQ

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)

def qq_login(req):
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        QQ_APP_ID = os.environ.get("QQ_APP_ID", config.get("QQ_APP_ID"))
        QQ_KEY = os.environ.get("QQ_KEY", config.get("QQ_KEY"))
        QQ_RECALL_URL = os.environ.get("QQ_RECALL_URL", config.get("QQ_RECALL_URL"))
    oauth_qq = OAuthQQ(QQ_APP_ID, QQ_KEY, QQ_RECALL_URL)
    url = oauth_qq.get_auth_url()
    return HttpResponseRedirect(url)
