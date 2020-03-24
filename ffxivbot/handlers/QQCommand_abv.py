from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
from bs4 import BeautifulSoup
import urllib
import logging
import time
import traceback
import re

class ABV:
    def __init__(self):
        self.table = 'fZodR9XQDSUm21yCkr6zBqiveYah8bt4xsWpHnJE7jL5VG3guMTKNPAwcF'
        self.tr = {}
        for i in range(58):
            self.tr[self.table[i]] = i
        self.s = [11,10,3,8,4,6]
        self.xor = 177451812
        self.add = 8728348608

    def bv2av(self, bv):
        r = 0
        for i in range(6):
            r += self.tr[bv[self.s[i]]] * 58 ** i
        return (r - self.add) ^ self.xor

    def av2bv(self, av):
        av = (av ^ self.xor) + self.add
        r = list('BV1  4 1 7  ')
        for i in range(6):
            r[self.s[i]] = self.table[av // 58 ** i % 58]
        return ''.join(r)

def QQCommand_abv(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        bot = kwargs["bot"]
        receive = kwargs["receive"]

        message_content = receive["message"].replace("/abv", "", 1).strip()
        msg = ""
        av = re.search(r"^(?:av|AV)?(\d+)$", message_content)
        bv = re.search(r"((?:BV)?[\d\w]+)", message_content)
        if message_content.find("help") == 0 or message_content == "":
            msg = (
                "/abv $av : 将Bilibili的av号转化为BV号\n"
                + "/abv $bv : 将Bilibili的BV号转化为av号"
            )
        elif av:
            av = int(av.group(1))
            abv = ABV()
            msg = abv.av2bv(av)
        elif bv:
            bv = bv.group(1)
            if not bv.startswith('BV'):
                bv = 'BV' + bv
            abv = ABV()
            msg = 'av' + str(abv.bv2av(bv))
        else:
            msg = "请输入av号或BV号自动转换"

        if isinstance(msg, str):
            msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        logging.error(e)
        traceback.print_exc()
    return action_list
