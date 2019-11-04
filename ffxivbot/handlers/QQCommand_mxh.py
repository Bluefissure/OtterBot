<<<<<<< HEAD
from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import os
import codecs
import logging
import traceback
import random
import json

def QQCommand_mxh(*args, **kwargs)
    try:
        bot = kwargs["bot"]
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        action_list = []
        msg = ""
        receive_msg = receive["message"].replace("/mxh","",1).strip()
        if receive_msg.find("help")==0 or receive_msg=="":
            msg="CP短打生成器,使用方法：/mxh 攻 受\n此功能只限用于休闲娱乐，所有故事均为匿名投稿提供。如有雷同，纯属巧合。 最终解释权归CP短打生成器作者所有。\nPowered by https://mxh-mini-apps.github.io/mxh-cp-stories/"
        else:
            receive_msg = receive_msg.split(" ")
            gg = receive_msg[0]
            mm = receive_msg[-1]
            mxh_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "text/mxh.json")
            mxh_js = open(mxh_file).read()
            text = random.choice(json.loads(mxh_js))
            for m in text["stories"]:
                msg += m+"\n"
            msg = msg.replace("<攻>",gg).replace("<受>",mm).replace(text["roles"]["gong"],gg).replace(text["roles"]["shou"],mm)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
=======
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
>>>>>>> d4c3072ab1af8fa6cdfed2785e6f0f7990dc1bbe
