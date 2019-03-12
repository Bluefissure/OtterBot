from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random


def QQCommand_random(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        try:
            num = int(receive["message"].replace("/random", ""))
            num = max(num, 0)
        except:
            num = 1000
        score = random.randint(1, num)
        msg = str(score)
        msg = "[CQ:at,qq=%s] 掷出了" % (receive["user_id"]) + msg + "点！"

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
