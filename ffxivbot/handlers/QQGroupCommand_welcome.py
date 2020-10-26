from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import html


def QQGroupCommand_welcome(*args, **kwargs):
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
        second_command_msg = receive["message"].replace("/welcome", "", 1).strip()
        second_command = second_command_msg.split(" ")[0].strip()
        if second_command == "set":
            if user_info["role"] != "owner" and user_info["role"] != "admin":
                msg = "仅群主与管理员有权限设置欢迎语"
            else:
                welcome_msg = second_command_msg.replace("set", "", 1).strip()
                group.welcome_msg = html.unescape(welcome_msg)
                group.save()
                msg = '欢迎语已设置成功，使用"/welcome demo"查看欢迎示例'
        elif second_command == "test" or second_command == "demo":
            msg = "[CQ:at,qq=%s] " % (user_id) + group.welcome_msg
        else:
            msg = '错误的命令，二级命令有:"set", "test", "demo"'

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return []
