import random
import sys
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
sys.path.append(FFXIVBOT_ROOT)
os.environ["DJANGO_SETTINGS_MODULE"] = "FFXIV.settings"
from FFXIV import settings
import django
from django.db import transaction

django.setup()
from channels.layers import get_channel_layer
from channels.exceptions import StopConsumer

channel_layer = get_channel_layer()
import traceback
import pika
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
import time
import re
import pytz
import datetime
from collections import OrderedDict
import binascii
import json
from asgiref.sync import async_to_sync
import ffxivbot.handlers as handlers
from ffxivbot.models import *
from ffxivbot.api_caller import ApiCaller
from ffxivbot.event_handler import EventHandler


USE_GRAFANA = getattr(settings, "USE_GRAFANA", False)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)
logging.basicConfig(
    format="%(levelname)s:%(asctime)s:%(name)s:%(message)s", level=logging.INFO
)
LOGGER = logging.getLogger(__name__)


class PikaConsumer(object):
    """This is based on the example consumer at 
    https://github.com/pika/pika/blob/master/examples/asynchronous_consumer_example.py
    """

    EXCHANGE = "message"
    EXCHANGE_TYPE = "topic"
    QUEUE = "ffxivbot"
    ROUTING_KEY = ""

    def __init__(self, amqp_url):
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url

    def connect(self):
        LOGGER.info("Connecting to %s", self._url)
        parameters = pika.URLParameters(self._url)

        return pika.SelectConnection(
            parameters, self.on_connection_open, stop_ioloop_on_close=False
        )

    def on_connection_open(self, unused_connection):
        LOGGER.info("Connection opened")
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        LOGGER.info("Adding connection close callback")
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            LOGGER.warning(
                "Connection closed, reopening in 5 seconds: (%s) %s",
                reply_code,
                reply_text,
            )
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        self._connection.ioloop.stop()
        if not self._closing:
            self._connection = self.connect()
            self._connection.ioloop.start()

    def open_channel(self):
        LOGGER.info("Creating a new channel")
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        LOGGER.info("Channel opened")
        self._channel = channel
        self._channel.basic_qos(prefetch_count=1)
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):
        LOGGER.info("Adding channel close callback")
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        LOGGER.warning(
            "Channel %i was closed: (%s) %s", channel, reply_code, reply_text
        )
        self._connection.close()

    def setup_exchange(self, exchange_name):
        LOGGER.info("Declaring exchange %s", exchange_name)
        self._channel.exchange_declare(
            self.on_exchange_declareok, exchange_name, self.EXCHANGE_TYPE
        )

    def on_exchange_declareok(self, unused_frame):
        LOGGER.info("Exchange declared")
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        LOGGER.info("Declaring queue %s", queue_name)
        self._channel.queue_declare(
            self.on_queue_declareok,
            queue_name,
            arguments={"x-max-priority": 20, "x-message-ttl": 60000},
        )

    def on_queue_declareok(self, method_frame):
        LOGGER.info(
            "Binding %s to %s with %s", self.EXCHANGE, self.QUEUE, self.ROUTING_KEY
        )
        self._channel.queue_bind(
            self.on_bindok, self.QUEUE, self.EXCHANGE, self.ROUTING_KEY
        )

    def on_bindok(self, unused_frame):
        LOGGER.info("Queue bound")
        self.start_consuming()

    def start_consuming(self):
        LOGGER.info("Issuing consumer related RPC commands")
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message, self.QUEUE)

    def add_on_cancel_callback(self):
        LOGGER.info("Adding consumer cancellation callback")
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        LOGGER.info("Consumer was cancelled remotely, shutting down: %r", method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        try:
            receive = json.loads(body)
            receive["pika_time"] = time.time()
            self_id = receive["self_id"]
            try:
                bot = QQBot.objects.get(user_id=self_id)
            except QQBot.DoesNotExist as e:
                LOGGER.error("bot {} does not exsit.".format(self_id))
                raise e
            api_caller = ApiCaller(bot)
            event_handler = EventHandler(bot, api_caller)
            config = json.load(open(CONFIG_PATH, encoding="utf-8"))
            already_reply = False
            if (
                receive["post_type"] == "meta_event"
                and receive["meta_event_type"] == "heartbeat"
            ):
                LOGGER.info(
                    "bot:{} Event heartbeat at time:{}".format(
                        self_id, int(time.time())
                    )
                )
                api_caller.call_api(
                    "get_status",
                    {},
                    "get_status:{}".format(self_id),
                    post_type=receive.get("reply_api_type", "websocket"),
                )

            if receive["post_type"] == "message":
                event_handler.on_message(receive, config=config)
            if receive["post_type"] == "request":
                event_handler.on_request(receive, config=config)
            if receive["post_type"] == "notice":
                event_handler.on_notice(receive, config=config)
        except Exception as e:
            traceback.print_exc()
            LOGGER.error(e)

        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        LOGGER.debug("Pid:%s Acknowledging message %s", os.getpid(), delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        if self._channel:
            LOGGER.info("Sending a Basic.Cancel RPC command to RabbitMQ")
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        LOGGER.info("RabbitMQ acknowledged the cancellation of the consumer")
        self.close_channel()

    def close_channel(self):
        LOGGER.info("Closing the channel")
        self._channel.close()

    def run(self):
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        LOGGER.info("Stopping")
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()
        LOGGER.info("Stopped")

    def close_connection(self):
        LOGGER.info("Closing connection")
        self._connection.close()


def main():
    logging.basicConfig(level=logging.INFO)
    pikapika = PikaConsumer("amqp://guest:guest@localhost:5672/?heartbeat=600")
    try:
        pikapika.run()
    except KeyboardInterrupt:
        pikapika.stop()


if __name__ == "__main__":
    main()
