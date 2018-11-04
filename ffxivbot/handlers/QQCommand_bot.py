from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random
import requests
import math

class QQCommand_bot(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_bot, self).__init__()
    def __call__(self, **kwargs):
        try:
            global_config = kwargs["global_config"]
            QQ_BASE_URL = global_config["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]

            msg = ""
            receive_msg = receive["message"].replace('/bot','',1).strip()
            second_command = receive_msg.split(" ")[0]
            second_msg = receive_msg.replace(second_command,"",1).strip()
            if(second_command=="token"):
                if(receive["message_type"]=="group"):
                    msg = "[CQ:at,qq={}] 你确定要在群里面申请token从而公之于众？".format(receive["user_id"])
                else:
                    (qquser, created) = QQUser.objects.get_or_create(user_id=receive["user_id"])
                    qquser.bot_token = second_msg
                    qquser.save()
                    qquser.refresh_from_db()
                    msg = "用户 {} 的token已被设定为：{}".format(qquser,qquser.bot_token)
            elif receive_msg=="":
                msg = "/bot token $token: 申请接收ACT插件消息时认证的token"
            else:
                msg = "无效的二级命令，二级命令有:\"token\""

            msg = msg.strip()
            if msg:
                reply_action = self.reply_message_action(receive, msg)
                action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)