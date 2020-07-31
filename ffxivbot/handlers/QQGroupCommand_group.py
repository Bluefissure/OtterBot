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
        second_command_msg = receive["message"].replace("/group", "", 1).strip()
        second_command = second_command_msg.split(" ")[0].strip()
        group_bots = json.loads(group.bots)
        if second_command == "update":
            msg = "群成员统计请求已发送"
            action_list.append(
                {
                    "action": "get_group_member_list",
                    "params": {"group_id": group_id},
                    "echo": "get_group_member_list:%s" % (group_id),
                }
            )
        elif user_info["role"] != "owner" and user_info["role"] != "admin":
            msg = "仅群主与管理员有权限管理群"
        elif second_command == "register":
            group.registered = True
            group.save()
            msg = "群{}注册成功".format(group_id)
        elif second_command == "info":
            msg = (
                "群号：{}\n".format(group.group_id)
                + "注册状态：{}\n".format(group.registered)
                + "API开启状态：{}\n".format(group.api)
                + "复读触发条件：{}/min {}%\n".format(group.repeat_length, group.repeat_prob)
                + "复读禁言阈值：{}\n".format(group.repeat_ban)
                + "投票禁言阈值：{}\n".format(group.ban_cnt)
                + "群成员数量：{}\n".format(len(json.loads(group.member_list)))
            )
            if group_bots:
                msg += "群机器人：{}\n".format(group_bots)
            msg = msg.strip()
        elif second_command == "api":
            enable = second_command_msg.replace(second_command, "", 1)
            if "enable" in enable:
                group.api = True
            elif "disable" in enable:
                group.api = False
            group.save(update_fields=["api"])
            msg = "群内已{}獭のAPI功能".format("开启" if group.api else "禁止")
        elif second_command == "bot":
            bot_id = second_command_msg.split(" ")[1].strip()
            if bot_id not in group_bots:
                group_bots.append(bot_id)
            group.bots = json.dumps(group_bots)
            group.save(update_fields=["bots"])
            msg = "群机器人：{}".format(group_bots)
        elif second_command == "bot_del":
            bot_id = second_command_msg.split(" ")[1].strip()
            if bot_id in group_bots:
                group_bots.remove(bot_id)
            group.bots = json.dumps(group_bots)
            group.save(update_fields=["bots"])
            msg = "群机器人：{}".format(group_bots)
        else:
            msg = '错误的命令，二级命令有:"register", "info", "api", "bot"'
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return []
