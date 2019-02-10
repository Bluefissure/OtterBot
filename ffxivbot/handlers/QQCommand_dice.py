from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import dice

def QQCommand_dice(*args, **kwargs):
    action_list = []
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        receive = kwargs["receive"]

        dice_msg = receive["message"].replace("/dice","",1).strip()
        # if "d" in dice_msg:
        #     try:
        #         cnt = int(dice_msg.split("d"))[0]
        #         assert(cnt<=100)
        #     except:
        #         cnt = 100
        msg = "[CQ:at,qq={}]".format(receive["user_id"])
        msg += str(dice.roll(dice_msg))
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
