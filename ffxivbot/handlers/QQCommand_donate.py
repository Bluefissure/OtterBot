from .QQUtils import *
from ffxivbot.models import *
import logging


def QQCommand_donate(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
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
