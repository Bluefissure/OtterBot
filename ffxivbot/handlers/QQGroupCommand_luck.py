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


def QQGroupCommand_luck(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        action_list = []
        receive = kwargs["receive"]
        receive = kwargs["receive"]
        user_id = receive["user_id"]

        msg = "[CQ:at,qq=%s] " % user_id + "\n"

        url = r'https://www.zgjm.net/chouqian/guanyinlingqian/%s.html' % get_page_num(user_id)
        s = requests.post(url=url, timeout=5)
        soup = BeautifulSoup(s.text, "html.parser")
        total = soup.select(".article-content > p")
        for elem in total:
            line = elem.get_text().strip()
            if len(line) != 0:
                msg = msg + elem.get_text().strip() + "\n"

        # pic_url = soup.select(".article-content > p > img")
        # for pic in pic_url:
        #     print(pic["src"])
        msg = msg + "\n每天只能抽一次哦~"

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
