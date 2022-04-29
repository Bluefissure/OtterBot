from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import requests
import logging
import random
import time
import traceback

def get_xialian(shanglian):
    r = requests.get(
        url = f"https://ai-backend.binwang.me/v0.2/couplet/{shanglian}",
        timeout=15,
    )
    r = r.json()
    if len(r["output"]) == 0:
        return ""
    return random.choice([i for i in r["output"] if i != ""])

def QQCommand_duilian(*args, **kwargs):
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
            message_content = receive["message"].replace("/duilian", "", 1).strip()
            msg = "default msg"
            if message_content.find("help") == 0 or message_content == "":
                msg = (
                    "/duilian $shanglian : 生成$shanglian的下联\n"
                    + "Powered by https://ai.binwang.me/couplet/"
                )
            else:
                shanglian = message_content
                xialian = get_xialian(shanglian)
                msg = f"上联：{shanglian}\n下联：{xialian}"

        if type(msg) == str:
            msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        logging.error(e)
        traceback.print_exc()
