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
        random_num = get_page_num(user_id)
        luck_data = LuckData.objects.filter(number=random_num)
        if luck_data.exists():
            luck_data = luck_data[0]
            if "text" in receive["message"]:
                text = luck_data.text
                msg = "[CQ:at,qq=%s]" % user_id + "\n" + text
            else:
                base64_str = luck_data.pic_base64
                print(base64_str)
                msg = "[CQ:at,qq=%s]" % user_id + "[CQ:image,file=base64://{}]\n".format(base64_str)
                msg = msg.strip()
        else:
            msg = "[CQ:at,qq=%s]" % user_id + "好像出了点问题，明天再试试吧~"

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
