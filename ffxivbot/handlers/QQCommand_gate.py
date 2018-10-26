from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random

class QQCommand_gate(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_gate, self).__init__()
    def __call__(self, **kwargs):
        try:
            global_config = kwargs["global_config"]
            QQ_BASE_URL = global_config["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]
            bot = kwargs["bot"]
            
            try:
                num = int(receive["message"].replace("/gate",""))
            except:
                num = 2
            num = min(num, 3)
            gate = random.randint(0,num-1)
            choose_list = [i for i in range(num)]
            random.shuffle(choose_list)
            gate_idx = choose_list.index(gate)
            gate_msg = "左边" if gate_idx==0 else "右边" if gate_idx==1 else "中间"
            msg = "掐指一算，[CQ:at,qq=%s] 应该走%s门，信%s没错！"%(receive["user_id"],gate_msg,bot.name)
            
            reply_action = self.reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)