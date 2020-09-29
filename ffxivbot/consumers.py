import traceback
import sys
import random
import pika
import gc
import urllib
from bs4 import BeautifulSoup
import logging
import hmac
import html
import codecs
import base64
import requests
import math
from hashlib import md5
from FFXIV import settings
import ffxivbot.handlers as handlers
from ffxivbot.models import *
import time
import os
import re
import pytz
import datetime
from collections import OrderedDict
import json
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from channels.exceptions import StopConsumer
from django.db import transaction

channel_layer = get_channel_layer()
logging.basicConfig(
    format="%(levelname)s:%(asctime)s:%(name)s:%(message)s", level=logging.INFO
)
LOGGER = logging.getLogger(__name__)
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", settings.BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)


class PikaPublisher:
    def __init__(self, username="guest", password="guest", queue="ffxivbot"):
        # print("initializing pika publisher")
        # traceback.print_stack()
        self.credentials = pika.PlainCredentials(username, password)
        self.queue = queue
        self.parameters = pika.ConnectionParameters(
            "127.0.0.1", 5672, "/", self.credentials, heartbeat=0
        )
        self.connection = pika.BlockingConnection(self.parameters)
        self.channel = self.connection.channel()
        self.priority_queue = {"x-max-priority": 20, "x-message-ttl": 60000}
        self.channel.queue_declare(queue=self.queue, arguments=self.priority_queue)

    def send(self, body="null", priority=1):
        if not self.connection.is_open:
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            self.priority_queue = {"x-max-priority": 20, "x-message-ttl": 60000}
            self.channel.queue_declare(queue=self.queue, arguments=self.priority_queue)
        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue,
            body=body,
            properties=pika.BasicProperties(
                content_type="text/plain", priority=priority
            ),
        )
        # self.connection.close()

    def exit(self):
        if self.connection.is_open:
            self.connection.close()

    def ping(self):
        self.connection.process_data_events()


# PUB = PikaPublisher()


class WSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        header_list = self.scope["headers"]
        headers = {}
        for (k, v) in header_list:
            headers[k.decode()] = v.decode()
        true_ip = None
        try:
            true_ip = headers["x-forwarded-for"]
        except BaseException:
            pass
        try:
            ws_self_id = headers["x-self-id"]
            # ws_client_role = headers["x-client-role"]
            ws_access_token = (
                headers.get("authorization", "empty_access_token")
                .replace("Token", "")
                .strip()
            )
            client_role = headers["x-client-role"]
            user_agent = headers["user-agent"]
            if client_role != "Universal":
                LOGGER.error("Unkown client_role: {}".format(client_role))
                # await self.close()
                return
            if "CQHttp" not in user_agent and "MiraiHttp" not in user_agent and "OneBot" not in user_agent:
                LOGGER.error(
                    "Unknown user_agent: {} for {}".format(user_agent, ws_self_id)
                )
                return
            elif "CQHttp" in user_agent:
                version = user_agent.replace("CQHttp/", "").split(".")
                if version < "4.14.1".split("."):
                    LOGGER.error(
                        "Unsupport user_agent: {} for {}".format(user_agent, ws_self_id)
                    )
                    return
            elif "OneBot" in user_agent and "Bearer" in ws_access_token:
                # onebot基于rfc6750往token加入了Bearer
                ws_access_token = ws_access_token.replace("Bearer", "").strip()


            bot = None
            # with transaction.atomic():

            # bot = QQBot.objects.select_for_update().get(user_id=ws_self_id,access_token=ws_access_token)
            bot = QQBot.objects.get(user_id=ws_self_id, access_token=ws_access_token)

            self.bot = bot
            self.bot_user_id = self.bot.user_id
            self.bot.event_time = int(time.time())
            self.bot.api_channel_name = self.channel_name
            self.bot.event_channel_name = self.channel_name
            LOGGER.debug("New Universal Connection:%s" % (self.channel_name))
            self.bot.save(
                update_fields=["event_time", "api_channel_name", "event_channel_name"]
            )
            LOGGER.debug(
                "Universal Channel connect from {} by channel:{}".format(
                    self.bot.user_id, self.bot.api_channel_name
                )
            )
            self.pub = PikaPublisher()
            await self.accept()
        except QQBot.DoesNotExist:
            LOGGER.error(
                "%s:%s:API:AUTH_FAIL from %s" % (ws_self_id, ws_access_token, true_ip)
            )
            # await self.close()
        except:
            LOGGER.error("Unauthed connection from %s" % (true_ip))
            LOGGER.error(headers)
            traceback.print_exc()
            # await self.close()

    async def disconnect(self, close_code):
        try:
            # self.pub.exit()
            disconnect = json.loads(self.bot.disconnections)
            cur_time = int(time.time())
            disconnect_from_last_hour = []
            for dis in disconnect:
                if dis >= cur_time - 3600:
                    disconnect_from_last_hour.append(dis)
            disconnect_from_last_hour.append(cur_time)
            disconnect = disconnect_from_last_hour
            while len(disconnect) > 100:
                disconnect = disconnect[1:]
            self.bot.disconnections = json.dumps(disconnect)
            self.bot.save(update_fields=["disconnections"])
            LOGGER.info(
                "Universal Channel disconnect from {} by channel:{} Live for {}s, {} disconnections".format(
                    self.bot.user_id,
                    self.channel_name,
                    int(time.time()) - int(self.bot.event_time),
                    len(disconnect),
                )
            )
            gc.collect()
        except BaseException:
            pass
        # raise StopConsumer

    async def receive(self, text_data):
        # try:
        #     # self.bot = QQBot.objects.select_for_update().get(user_id = self.bot_user_id)
        #     self.bot = QQBot.objects.get(user_id = self.bot_user_id)
        # except QQBot.DoesNotExist:
        #     LOGGER.error("QQBot.DoesNotExist:{}".format(self.bot_user_id))
        #     return
        receive = json.loads(text_data)
        # print("receiving data:{}\n============================".format(json.dumps(receive)))

        if "post_type" in receive.keys():
            self.bot.event_time = int(time.time())
            self.bot.save(update_fields=["event_time"])
            self.config = json.load(open(CONFIG_PATH, encoding="utf-8"))
            try:
                receive = json.loads(text_data)
                if (
                    receive["post_type"] == "meta_event"
                    and receive["meta_event_type"] == "heartbeat"
                ):
                    # LOGGER.info(
                    #     "bot:{} Event heartbeat at time:{}".format(
                    #         self.bot.user_id, int(time.time())
                    #     )
                    # )
                    self.pub.ping()
                    # await self.call_api("get_status",{},"get_status:{}".format(self.bot_user_id))
                self_id = receive["self_id"]

                if (
                    receive["post_type"] == "request"
                    or receive["post_type"] == "notice"
                ):
                    LOGGER.info("Dev Debugging........")
                    LOGGER.info(json.dumps(receive))

                if "message" in receive.keys():
                    # if int(self_id)==3299510002:
                    #     LOGGER.info("receving prototype message:{}".format(receive["message"]))
                    priority = 1
                    # try:
                    #     if len(json.loads(self.bot.group_list)) >= 10:
                    #         priority += 1
                    #     version_info = json.loads(self.bot.version_info)
                    #     coolq_edition = version_info["coolq_edition"] if version_info and "coolq_edition" in version_info.keys() else ""
                    #     if "Pro" in coolq_edition:
                    #         priority += 1
                    # except BaseException:
                    #     traceback.print_exc()
                    match_prefix = ["/", "\\", "[CQ:at,qq={}]".format(self_id)]
                    push_to_mq = any(
                        [receive["message"].startswith(x) for x in match_prefix]
                    )
                    if "group_id" in receive:
                        priority += 1
                        group_id = receive["group_id"]
                        (group, group_created) = QQGroup.objects.get_or_create(
                            group_id=group_id
                        )
                        # push_to_mq = (
                        #     push_to_mq
                        #     or (
                        #         (group.repeat_ban > 0)
                        #         or (group.repeat_length > 1 and group.repeat_prob > 0)
                        #     )
                        # )
                        group_bots = json.loads(group.bots)
                        if group_bots and (str(self_id) not in group_bots):
                            push_to_mq = False
                            if receive["message"].startswith("/group"):
                                push_to_mq = True
                    if push_to_mq:
                        receive["consumer_time"] = time.time()
                        text_data = json.dumps(receive)
                        self.pub.send(text_data, priority)
                    return

                if (
                    receive["post_type"] == "request"
                    or receive["post_type"] == "notice"
                ):
                    priority = 3
                    self.pub.send(text_data, priority)
            except Exception as e:
                LOGGER.error(
                    "Error {} while handling message {}".format(type(e), text_data)
                )
                traceback.print_exc()
            # self.bot.save()
        else:
            self.bot.api_time = int(time.time())
            self.bot.save(update_fields=["api_time"])
            if int(receive["retcode"]) != 0:
                if int(receive["retcode"]) == 1 and receive["status"] == "async":
                    LOGGER.warning("API waring:" + text_data)
                else:
                    LOGGER.error("API error:" + text_data)
            if "echo" in receive.keys() and receive["echo"] is not None:
                echo = receive["echo"]
                LOGGER.debug("echo:{} received".format(receive["echo"]))
                if "get_group_member_list" in echo:
                    group_id = echo.replace("get_group_member_list:", "").strip()
                    try:
                        # group = QQGroup.objects.select_for_update().get(group_id=group_id)
                        group = QQGroup.objects.get(group_id=group_id)
                        member_list = (
                            json.dumps(receive["data"]) if receive["data"] else "[]"
                        )
                        group.member_list = member_list
                        group.save(update_fields=["member_list"])
                        # await self.send_message("group", group_id, "群成员信息刷新成功")
                    except QQGroup.DoesNotExist:
                        LOGGER.error("QQGroup.DoesNotExist:{}".format(group_id))
                        return
                    LOGGER.debug("group %s member updated" % (group.group_id))
                if "get_group_list" in echo:
                    self.bot.group_list = json.dumps(receive["data"])
                    self.bot.save(update_fields=["group_list"])
                if "get_friend_list" in echo:
                    self.bot.friend_list = json.dumps(receive["data"])
                    self.bot.save(update_fields=["friend_list"])
                if "get_version_info" in echo:
                    self.bot.version_info = json.dumps(receive["data"])
                    self.bot.save(update_fields=["version_info"])
                if "get_status" in echo:
                    user_id = echo.split(":")[1]
                    if not receive["data"] or not receive["data"]["good"]:
                        LOGGER.error(
                            "bot:{} not good at time:{}".format(
                                user_id, int(time.time())
                            )
                        )
                    else:
                        LOGGER.debug(
                            "bot:{} Universal heartbeat at time:{}".format(
                                user_id, int(time.time())
                            )
                        )
            # self.bot.save()

    async def send_event(self, event):
        LOGGER.debug(
            "Universal Channel {} send_event with event:{}".format(
                self.channel_name, json.dumps(event)
            )
        )
        if "[CQ:at,qq=306401806]" in json.dumps(event):
            LOGGER.info(
                "Universal Channel {} send_event with event:{}".format(
                    self.channel_name, json.dumps(event)
                )
            )
        await self.send(event["text"])

    async def call_api(self, action, params, echo=None):
        # print("calling api:{} {}\n============================".format(json.dumps(action),json.dumps(params)))
        if "async" not in action and not echo:
            action = action + "_async"
        jdata = {"action": action, "params": params}
        if echo:
            jdata["echo"] = echo
        await self.send_event({"type": "send.event", "text": json.dumps(jdata)})

    async def send_message(self, private_group, uid, message):
        if private_group == "group":
            await self.call_api("send_group_msg", {"group_id": uid, "message": message})
        if private_group == "private":
            await self.call_api(
                "send_private_msg", {"user_id": uid, "message": message}
            )

    async def update_group_member_list(self, group_id):
        await self.call_api(
            "get_group_member_list",
            {"group_id": group_id},
            "get_group_member_list:%s" % (group_id),
        )

    async def delete_message(self, message_id):
        await self.call_api("delete_msg", {"message_id": message_id})

    async def group_ban(self, group_id, user_id, duration):
        json_data = {"group_id": group_id, "user_id": user_id, "duration": duration}
        await self.call_api("set_group_ban", json_data)

