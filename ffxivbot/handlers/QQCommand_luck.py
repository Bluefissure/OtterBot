from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import datetime
import hashlib
from bs4 import BeautifulSoup


def QQCommand_luck(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        bot = kwargs["bot"]
        random_num = get_page_num(user_id)
        luck_data = LuckData.objects.filter(number=random_num)
        if luck_data.exists():
            luck_data = luck_data.first()
            bot_version = (json.loads(bot.version_info)["coolq_edition"].lower()
                           if bot.version_info != '{}'
                           else "pro")
            if bot_version == "pro" and "text" not in receive["message"]:
                img = luck_data.img_url
                msg = "[CQ:at,qq=%s]\n" % user_id + "[CQ:image,file={}]".format(img)
            else:
                msg = "[CQ:at,qq=%s]\n" % user_id + luck_data.text
        else:
            msg = "[CQ:at,qq=%s]\n" % user_id + "好像出了点问题，明天再试试吧~"

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)


def get_page_num(QQnum):
    today = datetime.date.today()
    formatted_today = int(today.strftime('%y%m%d'))
    strnum = str(formatted_today * QQnum)

    md5 = hashlib.md5()
    md5.update(strnum.encode('utf-8'))
    res = md5.hexdigest()

    return int(res.upper(), 16) % 100 + 1
