from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random
import dice

class QQCommand_dice(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_dice, self).__init__()
    def __call__(self, **kwargs):
        try:
            QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]

            dice_msg = receive["message"].replace("/dice","",1).strip()
            msg = "[CQ:at,qq={}]".format(receive["user_id"])
            msg += str(dice.roll(dice_msg))
            reply_action = self.reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)
