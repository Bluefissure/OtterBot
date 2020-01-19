from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests


def QQCommand_nuannuan(*args, **kwargs):
    action_list = []
    bot = kwargs["bot"]
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        receive = kwargs["receive"]
        try:
            url = "http://nuannuan.yorushika.co:5000/"
            bot_version = (json.loads(bot.version_info)["coolq_edition"].lower()
                           if bot.version_info != '{}'
                           else "pro")
            if bot_version != "pro" or "text" in receive["message"]:
                url += "text/"
            r = requests.get(url=url, timeout=5)
            res = json.loads(r.text)
            if res["success"]:
                msg = res.get("content", "default content")
                msg += "\nPowered by 露儿[Yorushika]"
            else:
                msg = "Error"
        except Exception as e:
            msg = "Error: {}".format(type(e))
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
