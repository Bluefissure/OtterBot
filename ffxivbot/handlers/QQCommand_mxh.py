from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import os


def QQCommand_mxh(*args, **kwargs):
    action_list = []
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]

        receive = kwargs["receive"]

        msg = "default message"
        receive_msg = receive["message"]
        receive_msg = receive_msg.replace("/mxh", "", 1).strip()
        args = receive_msg.split(" ")
        if receive_msg.find("help") == 0 or receive_msg == "":
            msg = (
                    "梅溪湖cp短打生成器，参数格式：/mxh 攻 受\n" + "Powered by https://github.com/mxh-mini-apps/mxh-cp-stories"
            )
        elif len(args) < 2:
            msg = "参数格式错误：/mxh 攻 受"
        else:
            a_name = args[0].strip()
            b_name = args[1].strip()
            data_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "mxh_story.json")
            with open(data_path, 'r', encoding='UTF-8') as load_f:
                load_dict = json.load(load_f)
                stories = []
                for item in load_dict:
                    stories += item["stories"]

                story = ""
                while "<攻>" not in story:
                    story = random.sample(stories, 1)[0]

                story = story.replace('<攻>', a_name)
                story = story.replace('<受>', b_name)
                msg = story

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
