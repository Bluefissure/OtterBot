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
import websocket
import traceback
from django.db import connections

try:
    import thread
except ImportError:
    import _thread as thread

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ["DJANGO_SETTINGS_MODULE"] = "FFXIV.settings"
from FFXIV import settings

django.setup()
from ffxivbot.models import *
from consumers import PikaPublisher


def close_old_connections():
    for conn in connections.all():
        conn.close_if_unusable_or_obsolete()


def on_message(ws, message):
    global bot, publisher, token
    msg = json.loads(message)
    if msg["op"] == 0:
        print("Server >>> DISPATCH")
        try:
            print(json.dumps(msg, indent=4, sort_keys=True))
            if not msg["d"]["content"].startswith("/"):
                return
            data = {
                "self_id": bot.qqbot.user_id,
                "user_id": msg["d"]["author"]["id"],
                "time": time.time(),
                "consumer_time": time.time(),
                "post_type": "message",
                "message_type": "group",
                "group_id": msg["d"]["channel_id"],
                "channel_id": msg["d"]["channel_id"],
                "message": msg["d"]["content"],
                "reply_api_type": "tomon",
                "sender": {"role": "member"},
                "nonce": msg["d"]["nonce"],
            }
            text_data = json.dumps(data)
            priority = 1
            publisher.send(text_data, priority)
        except Exception as e:
            traceback.print_exc()
    elif msg["op"] == 1:
        print("Server >>> HEARTBEAT")
        ws.send(json.dumps({"d": {"token": token}, "op": 4}))
        print("Client >>> HEARTBEAT_ACK")
    elif msg["op"] == 2:
        print("Server >>> IDENTIFY")
        pass
    elif msg["op"] == 3:
        print("Server >>> HELLO")
        ws.send(json.dumps({"d": {"token": token}, "op": 1}))
        print("Client >>> HEARTBEAT")
    elif msg["op"] == 4:
        print("Server >>> HEARTBEAT_ACK")
    elif msg["op"] == 5:
        print("Server >>> VOICE_STATE_UPDATE")


def on_error(ws, error):
    print(error)


def on_close(ws):
    print("### closed ###")


def on_open(ws):
    global token

    def run(*args):
        ws.send(json.dumps({"d": {"token": token}, "op": 2}))
        # time.sleep(1)
        # ws.close()
        # print("thread terminating...")

    thread.start_new_thread(run, ())


if __name__ == "__main__":
    while True:
        try:
            bot = TomonBot.objects.all()[0]
            bot.auth()
            bot.refresh_from_db()
            token = bot.token
            publisher = PikaPublisher()
            ws = websocket.WebSocketApp(
                "{}".format("wss://gateway.tomon.co"),
                on_message=on_message,
                on_error=on_error,
                on_close=on_close,
            )
            ws.on_open = on_open
            ws.run_forever()
        except:
            close_old_connections()
            traceback.print_exc()
        print("Exit, sleep 60s......")
        time.sleep(60)

