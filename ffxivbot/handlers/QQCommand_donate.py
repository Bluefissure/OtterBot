from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

def QQCommand_donate(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        msg = [{"type":"text","data":{"text":"我很可爱(*╹▽╹*)请给我钱"}},
            {"type":"image","data":{"file":QQ_BASE_URL+"static/alipay.jpg"}},
            {"type":"image","data":{"file":QQ_BASE_URL+"static/redpack.png"}}]
        # msg = [{"type":"text","data":{"text":"我很可爱(*╹▽╹*)但是不要捐助辣獭獭买了好多零食吃"}}]

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
