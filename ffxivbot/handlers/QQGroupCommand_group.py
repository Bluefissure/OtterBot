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
        if(user_info["role"]!="owner" and user_info["role"]!="admin"):
            msg = "仅群主与管理员有权限管理群"
        else:
            if(second_command=="register"):
                group.registered = True
                group.save()
                msg = "群{}注册成功".format(group_id)
            elif(second_command=="info"):
                msg = "TODO"
            elif(second_command=="weibo"):
                interval = second_command_msg.replace(second_command,"",1)
                try:
                    group.subscription_trigger_time = int(interval)
                except:
                    group.subscription_trigger_time = 300
                group.save(update_fields=["subscription_trigger_time"])
                msg = "微博订阅时间被设定为{}s".format(group.subscription_trigger_time)
            elif(second_command=="api"):
                enable = second_command_msg.replace(second_command,"",1)
                if "enable" in enable:
                    group.api = True
                elif "disable" in enable:
                    group.api = False
                group.save(update_fields=["api"])
                msg = "群内已{}獭のAPI功能".format("开启" if group.api else "禁止")
            else:
                msg = "错误的命令，二级命令有:\"register\", \"info\", \"weibo\", \"api\""
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)