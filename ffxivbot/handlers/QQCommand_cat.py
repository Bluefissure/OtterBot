from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests


def QQCommand_cat(*args, **kwargs):
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        r = random.randint(1,6)
        if r <= 3:
            img_url = QQ_BASE_URL + "static/cat/%s.jpg" % (random.randint(0, 750))
        else:
            try:
                api_url = "https://api.thecatapi.com/v1/images/search"
                img_url = requests.get(api_url).json()[0]["url"]
            except:
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
