from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random

class QQCommand_random(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_random, self).__init__()
    def __call__(self, **kwargs):
        try:
            global_config = kwargs["global_config"]
            QQ_BASE_URL = global_config["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]

            try:
                num = int(receive["message"].replace("/random",""))
                num = max(num, 0)
            except:
                num = 1000
            score = random.randint(1,num)
            msg = str(score)
            msg = "[CQ:at,qq=%s] 掷出了"%(receive["user_id"])+msg+"点！"
            
            reply_action = self.reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)