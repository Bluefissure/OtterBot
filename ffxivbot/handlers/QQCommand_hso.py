from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random
import dice
import feedparser
import traceback
import requests
import time
from bs4 import BeautifulSoup

class QQCommand_hso(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_hso, self).__init__()
    def __call__(self, **kwargs):
        try:
            QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]
            bot = kwargs["bot"]
            msg = "好色哦"
            if(random.randint(0, 4)==0 or not bot.r18):
                msg = "好色哦"
            else:
                page = random.randint(1,50)
                api_url = "https://konachan.com/post.json?limit=20&page={}".format(page)
                r = requests.get(api_url)
                img_json = json.loads(r.text)
                if receive["message_type"]=="group":
                    tmp_list = []
                    for item in img_json:
                        if item["rating"]=="s":
                            tmp_list.append(item)
                    img_json = tmp_list
                idx = random.randint(0,len(img_json)-1)
                img = img_json[idx]
                msg = "[CQ:image,file={}]".format(img["sample_url"])

            reply_action = self.reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)
            traceback.print_exc()
