from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random


def QQCommand_cat(*args, **kwargs):
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        img_url = QQ_BASE_URL + "static/cat/%s.jpg" % (random.randint(0, 750))
        msg = "[CQ:image,file={}]".format(img_url)
        msg = [{"type": "image", "data": {"file": img_url},}]
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
