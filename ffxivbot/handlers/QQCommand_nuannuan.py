from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import requests_cache

def QQCommand_nuannuan(*args, **kwargs):
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        try:
            with requests_cache.disabled():
                r = requests.get(url="http://yotsuyu.yorushika.tk:5000/")
            res = json.loads(r.text)
            if res["success"]:
                msg = res["content"]
                msg += "\nPowered by 露儿[Yorushika]"
            else:
                msg = "Error"
        except Exception as e:
            msg = "Error: {}".format(e)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
