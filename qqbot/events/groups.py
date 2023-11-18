import json
import re
import requests
import urllib.parse
import os
import logging
from QQBot import QQBot
from .guilds import handle_quest, handle_search, handle_market

_log = logging.getLogger("QQBot Groups")

def on_group_at_message_create(message, qqbot: QQBot):
    _log.info(json.dumps(message, indent=2, ensure_ascii=False))
    data = message['d']
    group_id = data['group_openid']
    content = re.sub(r"<@!.*>", "", data['content']).strip()
    msg = None
    image = None
    if content.startswith("/ping"):
        qqbot.log.info(f"Get pinged from group:{group_id}")
        qqbot.reply_group_message(message, content="Pong!")
        return
    if content.startswith("/quest"):
        quest_name = content.replace("/quest", "").strip()
        msg_object = handle_quest(quest_name)
        if "ark" in msg_object:
            ark = msg_object["ark"]
        else:
            msg = msg_object["message"]
            # image = msg_object.get('image')
    if content.startswith("/search"):
        item_name = content.replace("/search", "").strip()
        msg_object = handle_search(item_name)
        if "ark" in msg_object:
            ark = msg_object["ark"]
        else:
            msg = msg_object["message"]
            msg = re.sub(r"https://garlandtools.cn/db/#item/\d+", "", msg)
    if content.startswith("/market") or content.startswith("/mitem"):
        args_str = content.replace("/mitem", "/market item").replace("/market", "").strip()
        args = args_str.split(" ")
        while '' in args:
            args.remove('')
        msg_object = handle_market(args)
        msg = msg_object["message"]
    if msg:
        qqbot.log.info(msg)
        if image:
            qqbot.log.info("Sending image %s", image)
            qqbot.reply_group_message(message, content=msg, image=image)
        else:
            qqbot.reply_group_message(message, content=msg)