from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import datetime
import hashlib


def QQCommand_luck(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]

        random_num = get_page_num(user_id)

        msg = "[CQ:at,qq=%s]" % user_id + \
              "[CQ:image, file=http://122.51.59.30:8080/static/luck_img/luck_%s.jpg]" % random_num

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
