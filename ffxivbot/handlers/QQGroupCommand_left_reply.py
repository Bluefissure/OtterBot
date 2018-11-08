from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

def QQGroupCommand_left_reply(*args, **kwargs):
        try:
            global_config = kwargs["global_config"]
            group = kwargs["group"]
            user_info = kwargs["user_info"]
            QQ_BASE_URL = global_config["QQ_BASE_URL"]
            action_list = []
            bot = kwargs["bot"]
            receive = kwargs["receive"]
            user_id = receive["user_id"]
            group_id = receive["group_id"]

            msg = "default msg"
            second_command_msg = receive["message"].replace("/left_reply","",1).strip()
            
            if(second_command_msg==""):
                msg = "本群剩余{}条{}聊天限额".format(group.left_reply_cnt,bot.name)
            else:
                second_command = second_command_msg.split(" ")[0].strip()
                if(second_command=="set"):
                    receive_msg = second_command_msg.replace(second_command,"",1).strip()
                    if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                        msg = "仅群主与管理员有权限设置群功能控制"
                    else:
                        try:
                            num = int(receive_msg)
                        except:
                            num = 100
                        group.left_reply_cnt = num
                        group.save()
                        msg = "群聊天限额被设置成剩余{}条".format(group.left_reply_cnt)
                else:
                    msg = "错误的命令，二级命令有:\"\",\"set\""

            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(reply_message_action(receive, msg))
            logging.error(e)