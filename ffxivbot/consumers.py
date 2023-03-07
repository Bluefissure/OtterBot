import re
import traceback
import pika
import gc
import logging
from FFXIV import settings
from ffxivbot.models import *
import time
import os
import json
import redis
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.layers import get_channel_layer
from asgiref.sync import sync_to_async
from asyncio.exceptions import CancelledError

channel_layer = get_channel_layer()
logging.basicConfig(
    format="%(levelname)s:%(asctime)s:%(name)s:%(message)s", level=logging.INFO
)
LOGGER = logging.getLogger(__name__)
REDIST_URL = "localhost" if os.environ.get('IS_DOCKER', '') != 'Docker' else 'redis'
# FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", settings.BASE_DIR)
# CONFIG_PATH = os.environ.get(
#     "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
# )


class PikaPublisher:
    def __init__(self, username="guest", password="guest", queue="ffxivbot"):
        self.credentials = pika.PlainCredentials(username, password)
        self.queue = queue
        self.parameters = pika.ConnectionParameters(
            "127.0.0.1", 5672, "/", self.credentials, heartbeat=0
        )
        self.priority_queue = {"x-max-priority": 20, "x-message-ttl": 60000}
        self.connection = None
        self.connect()

    def connect(self):
        if not self.connection or self.connection.is_closed:
            self.connection = pika.BlockingConnection(self.parameters)
            self.channel = self.connection.channel()
            self.channel.queue_declare(queue=self.queue, arguments=self.priority_queue)

    def _send(self, body="null", priority=1):
        self.channel.basic_publish(
            exchange="",
            routing_key=self.queue,
            body=body,
            properties=pika.BasicProperties(
                content_type="text/plain", priority=priority
            ),
        )

    def send(self, body="null", priority=1):
        try:
            self._send(body, priority)
        except pika.exceptions.ConnectionClosed:
            logging.info("Pika reconnecting to queue")
            self.connect()
            self._send(body, priority)

    def exit(self):
        if self.connection and self.connection.is_open:
            self.connection.close()

    def ping(self):
        self.connection.process_data_events()


class WSConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.redis = None
        self.pub = None
        self.bot = None
        header_list = self.scope["headers"]
        headers = {}
        for (k, v) in header_list:
            headers[k.decode()] = v.decode()
        true_ip = headers.get("x-forwarded-for", None)
        true_ip = headers.get("cf-connecting-ip", true_ip)
        try:
            ws_self_id = headers["x-self-id"]
            ws_access_token = (
                headers.get("authorization", "empty_access_token")
                .replace("Token", "")
                .strip()
            )
            client_role = headers["x-client-role"]
            user_agent = headers.get("user-agent", "Unknown")
            if client_role != "Universal":
                LOGGER.error("Unkown client_role: {}".format(client_role))
                await self.close()
                return
            if (
                "CQHttp" not in user_agent
                and "MiraiHttp" not in user_agent
                and "OneBot" not in user_agent
            ):
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
            else:
                LOGGER.error(f"Unkown UA: {user_agent}")
                await self.close()

            self.redis = redis.Redis(host=REDIST_URL, port=6379, decode_responses=True)
            if self.redis:
                bot_hash = f"bot_channel_name:{ws_self_id}"
                self.redis.set(bot_hash, self.channel_name, ex=3600*12)

            bot = None
            # with transaction.atomic():
            #   bot = QQBot.objects.select_for_update().get(user_id=ws_self_id,access_token=ws_access_token)
            try:
                bot = await sync_to_async(QQBot.objects.get, thread_sensitive=True)(user_id=ws_self_id, access_token=ws_access_token)
                if not bot:
                    return
                self.bot = bot
                self.bot_user_id = self.bot.user_id
                self.bot.event_time = int(time.time())
                self.bot.api_channel_name = self.channel_name
                self.bot.event_channel_name = self.channel_name
                LOGGER.info(
                    "New Universal Connection: %s of bot %s"
                    % (self.channel_name, self.bot.user_id)
                )
                await sync_to_async(self.bot.save, thread_sensitive=True)(
                    update_fields=["event_time", "api_channel_name", "event_channel_name"]
                )
            except CancelledError as e:
                LOGGER.error(
                    f"Bot {bot} update failed: {e}"
                )

            self.pub = PikaPublisher()
            await self.accept()
        except QQBot.DoesNotExist:
            LOGGER.error(
                "%s:%s:API:AUTH_FAIL from %s" % (ws_self_id, ws_access_token, true_ip)
            )
            await self.close()
        except:
            LOGGER.error("Unauthed connection from %s" % (true_ip))
            LOGGER.error(headers)
            traceback.print_exc()
            await self.close()

    async def redis_disconnect(self, *args):
        LOGGER.info("Redis of channel {} disconnected".format(self.channel_name))

    async def disconnect(self, close_code):
        LOGGER.info(
            "Universal Channel disconnect from channel:{} bot:{}".format(
                self.channel_name,
                self.bot.user_id if self.bot else None,
            )
        )
        if self.pub:
            self.pub.exit()
        gc.collect()

    async def receive(self, text_data):
        if not self.bot:
            LOGGER.error(
                "Bot of this connection is not set"
            )
            await self.close()
            return
        if not self.pub:
            LOGGER.error(
                "WSConsumer PikaPublisher is not initialized"
            )
            await self.close()
            return
        if self.redis:
            bot_hash = f"bot_channel_name:{self.bot.user_id}"
            redis_channel_name = self.redis.get(bot_hash)
            if redis_channel_name != self.channel_name:
                LOGGER.error(
                    f"Channel name mismatch \"{redis_channel_name}\" --- \"{self.channel_name}\""
                )
                await self.close()
                return
        receive = json.loads(text_data)

        if "post_type" in receive.keys():
            if self.redis:
                bot_hash = f"bot_event_time:{self.bot.user_id}"
                self.redis.set(bot_hash, str(int(time.time())), ex=3600)
            # self.bot.event_time = int(time.time())
            # await sync_to_async(self.bot.save, thread_sensitive=True)(update_fields=["event_time"])
            # with open(CONFIG_PATH, encoding="utf-8") as f:
            #     self.config = json.load(f)
            try:
                receive = json.loads(text_data)
                if (
                    receive["post_type"] == "meta_event"
                    and receive["meta_event_type"] == "heartbeat"
                ):
                    self.pub.ping()
                self_id = receive["self_id"]
                at_self_pattern = "\[CQ:at,qq={}(,text=.*)?\]".format(self_id)             
                if "message" in receive.keys():
                    if isinstance(receive["message"], list):
                        msg = ""
                        for block in receive["message"]:
                            if block["type"] == "text":
                                msg += block["data"]["text"]
                            elif block["type"] == "image":
                                msg += "[CQ:image,file={}]".format(
                                            block["data"].get("url", block["data"]["file"])
                                        )
                            elif block["type"] == "face":
                                msg += "[CQ:face,id={}]".format(block["data"]["id"])
                            elif block["type"] == "at":
                                msg += "[CQ:at,qq={}]".format(block["data"]["qq"])
                        receive["message"] = msg
                    priority = 1
                    chatting = re.search(at_self_pattern, receive.get("message", "")) is not None
                    push_to_mq = receive["message"].startswith("/") or receive["message"].startswith("\\") or chatting
                    if "group_id" in receive:
                        priority += 1
                        group_id = receive["group_id"]
                        (group, group_created) = await sync_to_async(QQGroup.objects.get_or_create)(
                            group_id=group_id
                        )
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
        else:
            # self.bot.api_time = int(time.time())
            # await sync_to_async(self.bot.save, thread_sensitive=True)(update_fields=["api_time"])
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
                        group = await sync_to_async(QQGroup.objects.get)(group_id=group_id)
                        member_list = (
                            json.dumps(receive["data"]) if receive["data"] else "[]"
                        )
                        group.member_list = member_list
                        await sync_to_async(group.save, thread_sensitive=True)(update_fields=["member_list"])
                        # await self.send_message("group", group_id, "群成员信息刷新成功")
                    except QQGroup.DoesNotExist:
                        LOGGER.error("QQGroup.DoesNotExist:{}".format(group_id))
                        return
                    LOGGER.debug("group %s member updated" % (group.group_id))
                if "get_group_list" in echo:
                    self.bot.group_list = json.dumps(receive["data"])
                    await sync_to_async(self.bot.save)(update_fields=["group_list"])
                if "get_friend_list" in echo:
                    self.bot.friend_list = json.dumps(receive["data"])
                    await sync_to_async(self.bot.save)(update_fields=["friend_list"])
                if "get_version_info" in echo:
                    self.bot.version_info = json.dumps(receive["data"])
                    await sync_to_async(self.bot.save)(update_fields=["version_info"])
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
