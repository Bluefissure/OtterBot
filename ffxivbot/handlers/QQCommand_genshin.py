from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
from django.db.models import Q
import logging
import json
import random
import requests
import traceback
import time
import copy
from subprocess import STDOUT, check_output
from urllib.parse import urlparse
from bs4 import BeautifulSoup

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
GENSHIN_ARTIFACT_RATER_ROOT = os.path.join(FFXIVBOT_ROOT, "../../Genshin-Artifact-Rater/")
GENSHIN_ARTIFACT_RATER_PYTHON = "/root/.pyenv/versions/venv-genshin/bin/python3.8"


def QQCommand_genshin(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        SMMS_TOKEN = global_config.get("SMMS_TOKEN", "")
        receive = kwargs["receive"]
        bot = kwargs["bot"]

        receive_msg = receive["message"].replace("/genshin", "", 1).strip()
        msg_list = receive_msg.split(" ")
        second_command = msg_list[0]
        if second_command == "" or second_command == "help":
            msg = "/genshin rate $image : 给圣遗物图片打分\n Powered by https://discord.gg/SyGmBxds3M"
        elif second_command == "rate":
            if len(msg_list) < 2:
                msg = "您输入的参数个数不足：\n/image upload $category $image : 给类别$category上传图片"
            else:
                img_url = get_CQ_image(receive_msg)
                cmd = [GENSHIN_ARTIFACT_RATER_PYTHON,
                    os.path.join(GENSHIN_ARTIFACT_RATER_ROOT, "rate_artifact.py"),
                    img_url]
                msg = check_output(cmd, stderr=STDOUT, timeout=15, cwd=GENSHIN_ARTIFACT_RATER_ROOT)
                msg = msg.decode()
                print("Genshin rater output:\n{}".format(msg))
                msg = "[CQ:at,qq={}]\n".format(receive["user_id"]) + msg
        else:
            msg = "支持的二级命令为 \"help\", \"rate\""
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc()
    return action_list
