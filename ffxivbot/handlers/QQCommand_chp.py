from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import requests

def QQCommand_chp(*args, **kwargs):
    action_list = []
    QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
    receive = kwargs["receive"]
    try:
        url = "https://api.muxiaoguo.cn/api/caihongpi"
        r = requests.get(url=url, timeout=5)
        msg = r.json()["data"]["comment"]
    except Exception as e:
        msg = "Error: {}".format(type(e))
    reply_action = reply_message_action(receive, msg)
    action_list.append(reply_action)
    return action_list