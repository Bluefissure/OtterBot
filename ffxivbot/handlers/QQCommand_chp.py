from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import requests

def QQCommand_chp(*args, **kwargs):
    action_list = []
    receive = kwargs["receive"]
    try:
        url = "https://api.shadiao.app/chp"
        r = requests.get(url=url, timeout=5)
        msg = r.json()["data"]["text"]
    except Exception as e:
        msg = "Error: {}".format(type(e))
    reply_action = reply_message_action(receive, msg)
    action_list.append(reply_action)
    return action_list