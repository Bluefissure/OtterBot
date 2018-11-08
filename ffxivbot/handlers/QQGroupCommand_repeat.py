from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

def QQGroupCommand_repeat(*args, **kwargs):
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
        if(user_info["role"]=="owner" or user_info["role"]=="admin"):
            msg = "仅非群主与管理员有权限开启复读机系统"
        else:
            ori_msg = receive["message"].replace("/repeat","",1).strip()
            ori_msg = ori_msg.split(' ')
            if(len(ori_msg)<2):
                msg = "请复读机条数与复读概率（/repeat $times $prob）"
            else:
                try:
                    group.repeat_length = max(int(ori_msg[0]),2)
                    group.repeat_prob = min(int(ori_msg[1]),50)
                except Exception as e:
                    group.repeat_length = 2
                    group.repeat_prob = 50
                group.save()
                msg = "复读机系统已启动，复读概率为{}/min后的{}%".format(group.repeat_length,group.repeat_prob)            

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)