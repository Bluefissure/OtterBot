from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random

class QQCommand_bird(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_bird, self).__init__()
    def __call__(self, **kwargs):
        try:
            QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]
            jpg_cnt = 182
            gif_cnt = 5
            png_cnt = 65
            idx = random.randint(1,jpg_cnt+gif_cnt+png_cnt)
            img_path = "static/bird/%s.jpg"%(idx) if idx<=jpg_cnt else ("static/bird/%s.gif"%(idx-jpg_cnt) if idx-jpg_cnt<=gif_cnt else "static/bird/%s.png"%(idx-jpg_cnt-gif_cnt))
            msg = [{"type":"image","data":{"file":QQ_BASE_URL+img_path}}]

            reply_action = self.reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)
