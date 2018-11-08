from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

def QQCommand_10(*args, **kwargs):
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        msg = [{"type":"image","data":{"file":QQ_BASE_URL+"static/10/%s.jpg"%(random.randint(1,281))}}]
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
