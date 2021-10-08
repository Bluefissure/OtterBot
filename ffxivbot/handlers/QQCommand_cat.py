from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests


def QQCommand_cat(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        r = random.randint(1,6)
        try:
            api_url = "https://api.thecatapi.com/v1/images/search"
            img_url = requests.get(api_url).json()[0]["url"]
            msg = "[CQ:image,file={}]".format(img_url)
            msg = [{"type": "image", "data": {"file": img_url},}]
        except:
            msg = "Error get cat."
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
