from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

def QQCommand_waifu(*args, **kwargs):
    action_list = []
    try:
        receive = kwargs["receive"]
        msg = [{"type":"image","data":{"file":"https://www.thiswaifudoesnotexist.net/example-{}.jpg".format(random.randint(0, 70000))}}]
        print(msg)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
