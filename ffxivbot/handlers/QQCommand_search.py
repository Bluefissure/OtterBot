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
import traceback


def QQCommand_search(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        FF14WIKI_API_URL = global_config["FF14WIKI_API_URL"]
        FF14WIKI_BASE_URL = global_config["FF14WIKI_BASE_URL"]
        action_list = []

        receive = kwargs["receive"]

        name = receive["message"].replace("/search", "").strip()

        res_data = search_item(name, FF14WIKI_BASE_URL, FF14WIKI_API_URL)

        if isinstance(res_data, dict):
            msg = [{"type": "share", "data": res_data}]
        elif isinstance(res_data, str):
            msg = res_data
        else:
            msg = '在最终幻想XIV中没有找到"{}"'.format(name)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
