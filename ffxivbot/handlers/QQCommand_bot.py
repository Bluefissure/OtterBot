from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import math

def QQCommand_bot(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        bot = kwargs["bot"]

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
        elif receive_msg=="update":
            user_id = receive["user_id"]
            if(int(user_id)!=int(bot.owner_id)):
                msg = "仅机器人领养者能刷新机器人状态"
            else:
                action_list.append({
                    "action":"get_group_list",
                    "params":{},
                    "echo":"get_group_list",
                })
                action_list.append({
                    "action":"_get_friend_list",
                    "params":{"flat":True},
                    "echo":"_get_friend_list",
                })
                action_list.append({
                    "action":"get_version_info",
                    "params":{},
                    "echo":"get_version_info",
                })
                msg = "机器人状态统计请求已发送"

        elif receive_msg=="":
            msg = "/bot token $token: 申请接收ACT插件消息时认证的token\n"+\
                "/bot update: 更新机器人统计信息\n"
        else:
            msg = "无效的二级命令，二级命令有:\"token\",\"update\""

        msg = msg.strip() 
        if msg:
            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)