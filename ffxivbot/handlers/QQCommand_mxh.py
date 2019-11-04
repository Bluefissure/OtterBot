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
