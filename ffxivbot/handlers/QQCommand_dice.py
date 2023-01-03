from .QQUtils import *
from ffxivbot.models import *
import logging
import dice


def QQCommand_dice(*args, **kwargs):
    action_list = []
    try:
        receive = kwargs["receive"]

        dice_msg = receive["message"].replace("/dice", "", 1).strip()
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
