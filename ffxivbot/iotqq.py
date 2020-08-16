#!/usr/bin/env python3
import sys
import os
import django
import re
import json
import time
import requests
import string
import random
import codecs
import urllib
import base64
import logging
import csv
import argparse
import asyncio
import socketio
import traceback

try:
    import thread
except ImportError:
    import _thread as thread

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "FFXIV.settings"
from FFXIV import settings

django.setup()
from ffxivbot.models import QQGroup, QQBot
from consumers import PikaPublisher


def get_config():
    parser = argparse.ArgumentParser(description="Wrapper for IOTQQ")
    parser.add_argument("-q", "--qq", type=int, help="User id of the bot.")
    # Parse args.
    args = parser.parse_args()
    return args


def OnGroupMsgs(msg):
    global bot, publisher
    msg = msg["CurrentPacket"]["Data"]
    try:
        try:
            msg["Content"] = json.loads(msg["Content"])
        except json.decoder.JSONDecodeError:
            pass
        print(json.dumps(msg, indent=4, sort_keys=True))
        raw_msg = (
            msg["Content"]
            if isinstance(msg["Content"], str)
            else msg["Content"].get("Content", "")
        )
        raw_msg = raw_msg.strip()
        if "GroupPic" in msg["Content"]:
            raw_msg += " [CQ:image,url={}]".format(msg["Content"]["GroupPic"][0]["Url"])
        print(raw_msg)
        if not raw_msg.startswith("/"):
            return
        member_role = "member"
        try:
            group = QQGroup.objects.get(group_id=msg["FromGroupId"])
            member_list = json.loads(group.member_list)
            for member in member_list:
                if member["user_id"] == msg["FromUserId"]:
                    member_role = member["role"]
                    break
        except QQGroup.DoesNotExist:
            pass
        data = {
            "self_id": bot.user_id,
            "user_id": msg["FromUserId"],
            "time": msg["MsgTime"],
            "consumer_time": time.time(),
            "post_type": "message",
            "message_type": "group",
            "group_id": msg["FromGroupId"],
            "message": raw_msg,
            "reply_api_type": "iotqq",
            "sender": {"role": member_role},
        }
        text_data = json.dumps(data)
        priority = 1
        publisher.send(text_data, priority)
    except Exception as e:
        traceback.print_exc()


class PyIotqq:
    def __init__(
        self, robotqq: str, socketio_url: str, socketio_path: str, auth: str = None
    ):
        self.robotqq = robotqq
        self.sio = socketio.Client()
        headers = {}
        if auth:
            headers.update(
                {"Authorization": "Basic " + base64.b64encode(auth.encode()).decode()}
            )
        self.sio.connect(
            socketio_url,
            socketio_path=socketio_path,
            headers=headers,
            transports=["websocket"],
        )
        self.sio.event(self.connect)

    def connect(self):
        print("connected to server")
        self.sio.emit("GetWebConn", self.robotqq)

        while True:
            self.sio.emit("GetWebConn", self.robotqq)
            # self.webapi.keep_alive()
            time.sleep(30)


if __name__ == "__main__":
    args = get_config()
    assert args.qq, "Please specify the bot you want to connect to."
    bot = QQBot.objects.get(user_id=args.qq)
    publisher = PikaPublisher()
    assert bot.iotqq_url, "IOTQQ callback url is missing for QQBot {}.".format(args.qq)
    socketio_path = "/socket.io"
    pyiotqq = PyIotqq(bot.user_id, bot.iotqq_url, socketio_path, bot.iotqq_auth)
    pyiotqq.sio.on("OnGroupMsgs", OnGroupMsgs)
