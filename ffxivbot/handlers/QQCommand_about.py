from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random


def QQCommand_about(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        res_data = {
            "url": "https://github.com/Bluefissure/FFXIVBOT",
            "title": "FFXIVBOT",
            "content": "by Bluefissure",
            "image": "https://i.loli.net/2018/05/06/5aeeda6f1fd4f.png",
        }
        msg = [{"type": "share", "data": res_data}]

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
