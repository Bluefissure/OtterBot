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


def search_word(word):
    urlword = urllib.parse.quote(word)
    url = "https://api.imjad.cn/cloudmusic/?type=search&s={}".format(urlword)
    r = requests.get(url=url)
    jres = json.loads(r.text)
    status_code = jres["code"]
    if int(status_code) == 200 and int(jres["result"]["songCount"]) > 0:
        songs = jres["result"]["songs"]
        song = songs[0]
        song_id = song["id"]
        url = "https://api.imjad.cn/cloudmusic/?type=song&id={}".format(song_id)
        r = requests.get(url=url)
        song_res = json.loads(r.text)
        song_data = song_res["data"][0]
        msg = [
            {
                "type": "music",
                "data": {
                    "type": "163",
                    "id": "{}".format(song_id)
                },
            }
        ]
    else:
        msg = '未能找到"{}"对应歌曲'.format(word)
    return msg


def QQCommand_music(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        FF14WIKI_API_URL = global_config["FF14WIKI_API_URL"]
        FF14WIKI_BASE_URL = global_config["FF14WIKI_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        bot = kwargs["bot"]
        if time.time() < bot.api_time + bot.long_query_interval:
            msg = "技能冷却中"
        else:
            message_content = receive["message"].replace("/music", "", 1).strip()
            msg = "default msg"
            if message_content.find("help") == 0 or message_content == "":
                msg = (
                    "/music $name : 搜索关键词$name的歌曲\n" + "Powered by https://api.imjad.cn"
                )
            else:
                word = message_content
                msg = search_word(word)

        if type(msg) == str:
            msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        logging.error(e)
        traceback.print_exc()
