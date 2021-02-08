from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import requests


def QQCommand_dog(*args, **kwargs):
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        try:
            api_url = "https://api.thedogapi.com/v1/images/search"
            img_url = requests.get(api_url).json()[0]["url"]
        except Exception as dogapi:
            api_url = "https://dog.ceo/api/breeds/image/random"
            img_url = requests.get(api_url).json()["message"]
            logging.error(dogapi)
        msg = "[CQ:image,file={}]".format(img_url)
        msg = [{"type": "image", "data": {"file": img_url},}]
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
