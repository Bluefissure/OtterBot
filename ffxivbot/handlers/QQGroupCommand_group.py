from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

def QQGroupCommand_group(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]

        msg = "default msg"
        second_command_msg = receive["message"].replace("/group","",1).strip()
        second_command = second_command_msg.split(" ")[0].strip()
        if(second_command=="register"):
            if(user_info["role"]!="owner"):
                msg = "仅群主有权限注册"
            else:
                group.registered = True
                group.save()
                msg = "群{}注册成功".format(group_id)
        elif(second_command=="info"):
            msg = "TODO"
        else:
            msg = "错误的命令，二级命令有:\"register\", \"info\""
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)