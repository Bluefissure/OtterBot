from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
def QQGroupCommand_zibi(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        member_list = kwargs["member_list"]
        bot = kwargs["bot"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]
        msg =""
        second_command_msg = receive["message"].replace("/zibi","",1).strip()
        second_command = second_command_msg.split(" ")[0].strip()
        if(second_command=="" or second_command=="help"):
            msg = "/zibi $time: 自闭$time分钟"
        else:
            ban_time = second_command
            ban_action = group_ban_action(group_id,user_id,int(second_command)*60)
            action_list.append(ban_action)
            msg = "去我窝里自闭吧，还挺大的~"
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        logging.error(e)

