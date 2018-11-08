from .QQEventHandler import QQEventHandler
from .QQUtils import *
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

alter_tags = {
    "萝莉":"loli",
    "fate":"fate_(series)",
    "FATE":"fate_(series)",
    "Fate":"fate_(series)",
    "东方":"touhou"
}


def QQCommand_hso(*args, **kwargs):
        try:
            QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]
            bot = kwargs["bot"]
            msg = "好色哦"
            if(random.randint(0, 4)==0 or not bot.r18):
                msg = "好色哦"
            else:
                second_command_msg = receive["message"].replace("/hso","",1).strip()
                page = random.randint(1,50)
                params = "limit=20&page={}".format(page)
                if(second_command_msg!=""):
                    for alter in alter_tags.keys():
                        second_command_msg = second_command_msg.replace(alter,alter_tags[alter])
                    params = "tags={}".format(second_command_msg)
                api_url = "https://konachan.com/post.json?{}".format(params)
                r = requests.get(api_url)
                img_json = json.loads(r.text)

                if receive["message_type"]=="group":
                    tmp_list = []
                    for item in img_json:
                        if item["rating"]=="s":
                            tmp_list.append(item)
                    img_json = tmp_list

                if(len(img_json)==0):
                    msg = "未能找到所需图片"
                else:
                    idx = random.randint(0,len(img_json)-1)
                    img = img_json[idx]
                    msg = "[CQ:image,file={}]".format(img["sample_url"])

            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(reply_message_action(receive, msg))
            logging.error(e)
            traceback.print_exc()
