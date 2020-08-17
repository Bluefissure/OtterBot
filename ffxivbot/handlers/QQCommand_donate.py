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
        # msg = [{"type":"text","data":{"text":"我很可爱(*╹▽╹*)请给我钱"}},
        #     {"type":"image","data":{"file":QQ_BASE_URL+"static/alipay.jpg"}},
        #     {"type":"image","data":{"file":QQ_BASE_URL+"static/redpack.png"}}]
        # msg = [{"type":"text","data":{"text":"我很可爱(*╹▽╹*)但是不要捐助辣獭獭买了好多零食吃"}}]
        msg = [
            {
                "type": "share",
                "data": {
                    "url": "https://afdian.net/@bluefissure",
                    "title": "选择赞助獭獭的方案 | 爱发电",
                    "content": "来看看 Bluefissure 为你的赞助准备了什么奖励吧！",
                    "image": "https://i.loli.net/2020/08/17/m8Z1dxNPF7obqzK.png",
                },
            }
        ]
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
