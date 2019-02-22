from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import copy

def QQGroupCommand_command(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]

        COMMAND = copy.deepcopy(kwargs["commands"])
        COMMAND.update(kwargs["group_commands"])
        COMMAND.update(kwargs["alter_commands"])
        COMMAND.update({"/chat":"聊天功能","/reply":"自定义回复"})
        COMMAND = COMMAND.keys()
        group_commands = json.loads(group.commands)
        msg = "default msg"
        second_command_msg = receive["message"].replace("/command","",1).strip()
        second_command = second_command_msg.split(" ")[0].strip()
        if(second_command=="disable"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin"):
                msg = "仅群主与管理员有权限设置群功能控制"
            else:
                commands = second_command_msg.replace('disable','',1).split(" ")
                ok_commands = []
                for item in commands:
                    if item in COMMAND:
                        group_commands[item] = "disable"
                        ok_commands.append(item)
                group.commands = json.dumps(group_commands)
                group.save()
                msg = " ".join(ok_commands)
                msg += "功能已关闭"
        elif(second_command=="enable"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin"):
                msg = "仅群主与管理员有权限设置群功能控制"
            else:
                commands = second_command_msg.replace('enable','',1).split(" ")
                ok_commands = []
                for item in commands:
                    if item in COMMAND:
                        group_commands[item] = "enable"
                        ok_commands.append(item)
                group.commands = json.dumps(group_commands)
                group.save()
                msg = " ".join(ok_commands)
                msg += "功能已启用"
        elif(second_command=="clear"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin"):
                msg = "仅群主与管理员有权限设置群功能控制"
            else:
                group.commands = "{}"
                group.save()
                msg = "群功能已重置"
        elif(second_command=="list"):
            msg = "本群机器人功能启用情况如下：(未出现功能默认启用)\n"
            for k in group_commands.keys():
                v = group_commands[k]
                msg += "{}:{}\n".format(k, v)
            msg = msg.strip()
        elif(second_command==""):
            msg = "请使用\"/command (disable/enable) /$key\"来禁用/启用相关功能，某些不需要命令的功能关闭方法如下"
            msg += "\n\t聊天功能：关闭/chat功能即可"
            msg += "\n\t复读（禁言）功能：使用相关命令设置阈值为-1"
            msg += "\n\t微博监控功能：清空群内订阅微博用户"
        else:
            msg = "错误的命令，二级命令有:\"disable\", \"enable\", \"clear\", \"list\""

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)