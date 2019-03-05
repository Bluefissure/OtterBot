import random
import sys
import os
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", "/root/FFXIVBOT/")
sys.path.append(FFXIVBOT_ROOT)
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIV.settings'
from FFXIV import settings
import django
from django.db import transaction
django.setup()
from channels.layers import get_channel_layer 
from channels.exceptions import StopConsumer
channel_layer = get_channel_layer()
from asgiref.sync import async_to_sync
import json
from collections import OrderedDict
import datetime
import pytz
import re
import pymysql
import time
from ffxivbot.models import *
import ffxivbot.handlers as handlers
from hashlib import md5
import math
import requests
import base64
import random,sys
import traceback  
import codecs
import html
import hmac
import logging
from bs4 import BeautifulSoup
import urllib
import pika

CONFIG_PATH = os.environ.get("FFXIVBOT_CONFIG", FFXIVBOT_ROOT + "ffxivbot/config.json")

def handle_message(bot, message):
    new_message = message
    if isinstance(message, list):
        new_message = []
        for idx, msg in enumerate(message):
            if msg["type"]=="share" and bot.share_banned:
                share_data = msg["data"]
                new_message.append({
                    "type": "image",
                    "data": {
                        "file": share_data["image"],
                        "url": share_data["image"]
                    }
                })
                new_message.append({
                    "type":"text",
                    "data":{
                        "text":"{}\n{}\n{}".format(
                                            share_data["title"],
                                            share_data["content"],
                                            share_data["url"])
                    }
                })
            else:
                new_message.append(msg)

    return new_message

def call_api(bot, action, params, echo=None):
    # print("calling api:{} {}\n============================".format(json.dumps(action),json.dumps(params)))
    if("async" not in action and not echo):
        action = action + "_async"
    if "send_" in action and "_msg" in action:
        params["message"] = handle_message(bot, params["message"])
    jdata = {
        "action":action,
        "params":params,
    }
    if echo:
        jdata["echo"] = echo
    async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})

def send_message(bot, private_group, uid, message):
    if(private_group=="group"):
       call_api(bot, "send_group_msg", {"group_id":uid,"message":message})
    if(private_group=="private"):
       call_api(bot, "send_private_msg", {"user_id":uid,"message":message})

def update_group_member_list(bot, group_id):
    call_api(bot, "get_group_member_list",{"group_id":group_id},"get_group_member_list:%s"%(group_id))


class PikaException(Exception):
    '''
    Custom exception types
    '''
    def __init__(self, message="Default PikaException"):
        Exception.__init__(self, message)

# LOG_FORMAT = ('%(levelname) -10s %(asctime)s %(name) -30s %(funcName) '
#               '-35s %(lineno) -5d: %(message)s')
LOGGER = logging.getLogger(__name__)


class PikaConsumer(object):
    """This is an example consumer that will handle unexpected interactions
    with RabbitMQ such as channel and connection closures.

    If RabbitMQ closes the connection, it will reopen it. You should
    look at the output, as there are limited reasons why the connection may
    be closed, which usually are tied to permission related issues or
    socket timeouts.

    If the channel is closed, it will indicate a problem with one of the
    commands that were issued and that should surface in the output as well.

    """
    EXCHANGE = 'message'
    EXCHANGE_TYPE = 'topic'
    QUEUE = 'ffxivbot'
    ROUTING_KEY = ''

    def __init__(self, amqp_url):
        """Create a new instance of the consumer class, passing in the AMQP
        URL used to connect to RabbitMQ.

        :param str amqp_url: The AMQP url to connect with

        """
        self._connection = None
        self._channel = None
        self._closing = False
        self._consumer_tag = None
        self._url = amqp_url

    def connect(self):
        """This method connects to RabbitMQ, returning the connection handle.
        When the connection is established, the on_connection_open method
        will be invoked by pika.

        :rtype: pika.SelectConnection

        """
        LOGGER.info('Connecting to %s', self._url)
        parameters = pika.URLParameters(self._url)

        return pika.SelectConnection(parameters,
                                     self.on_connection_open,
                                     stop_ioloop_on_close=False)

    def on_connection_open(self, unused_connection):
        """This method is called by pika once the connection to RabbitMQ has
        been established. It passes the handle to the connection object in
        case we need it, but in this case, we'll just mark it unused.

        :type unused_connection: pika.SelectConnection

        """
        LOGGER.info('Connection opened')
        self.add_on_connection_close_callback()
        self.open_channel()

    def add_on_connection_close_callback(self):
        """This method adds an on close callback that will be invoked by pika
        when RabbitMQ closes the connection to the publisher unexpectedly.

        """
        LOGGER.info('Adding connection close callback')
        self._connection.add_on_close_callback(self.on_connection_closed)

    def on_connection_closed(self, connection, reply_code, reply_text):
        """This method is invoked by pika when the connection to RabbitMQ is
        closed unexpectedly. Since it is unexpected, we will reconnect to
        RabbitMQ if it disconnects.

        :param pika.connection.Connection connection: The closed connection obj
        :param int reply_code: The server provided reply_code if given
        :param str reply_text: The server provided reply_text if given

        """
        self._channel = None
        if self._closing:
            self._connection.ioloop.stop()
        else:
            LOGGER.warning('Connection closed, reopening in 5 seconds: (%s) %s',
                           reply_code, reply_text)
            self._connection.add_timeout(5, self.reconnect)

    def reconnect(self):
        """Will be invoked by the IOLoop timer if the connection is
        closed. See the on_connection_closed method.

        """
        # This is the old connection IOLoop instance, stop its ioloop
        self._connection.ioloop.stop()

        if not self._closing:

            # Create a new connection
            self._connection = self.connect()

            # There is now a new connection, needs a new ioloop to run
            self._connection.ioloop.start()

    def open_channel(self):
        """Open a new channel with RabbitMQ by issuing the Channel.Open RPC
        command. When RabbitMQ responds that the channel is open, the
        on_channel_open callback will be invoked by pika.

        """
        LOGGER.info('Creating a new channel')
        self._connection.channel(on_open_callback=self.on_channel_open)

    def on_channel_open(self, channel):
        """This method is invoked by pika when the channel has been opened.
        The channel object is passed in so we can make use of it.

        Since the channel is now open, we'll declare the exchange to use.

        :param pika.channel.Channel channel: The channel object

        """
        LOGGER.info('Channel opened')
        self._channel = channel
        self._channel.basic_qos(prefetch_count=1)
        self.add_on_channel_close_callback()
        self.setup_exchange(self.EXCHANGE)

    def add_on_channel_close_callback(self):
        """This method tells pika to call the on_channel_closed method if
        RabbitMQ unexpectedly closes the channel.

        """
        LOGGER.info('Adding channel close callback')
        self._channel.add_on_close_callback(self.on_channel_closed)

    def on_channel_closed(self, channel, reply_code, reply_text):
        """Invoked by pika when RabbitMQ unexpectedly closes the channel.
        Channels are usually closed if you attempt to do something that
        violates the protocol, such as re-declare an exchange or queue with
        different parameters. In this case, we'll close the connection
        to shutdown the object.

        :param pika.channel.Channel: The closed channel
        :param int reply_code: The numeric reason the channel was closed
        :param str reply_text: The text reason the channel was closed

        """
        LOGGER.warning('Channel %i was closed: (%s) %s',
                       channel, reply_code, reply_text)
        self._connection.close()

    def setup_exchange(self, exchange_name):
        """Setup the exchange on RabbitMQ by invoking the Exchange.Declare RPC
        command. When it is complete, the on_exchange_declareok method will
        be invoked by pika.

        :param str|unicode exchange_name: The name of the exchange to declare

        """
        LOGGER.info('Declaring exchange %s', exchange_name)
        self._channel.exchange_declare(self.on_exchange_declareok,
                                       exchange_name,
                                       self.EXCHANGE_TYPE)

    def on_exchange_declareok(self, unused_frame):
        """Invoked by pika when RabbitMQ has finished the Exchange.Declare RPC
        command.

        :param pika.Frame.Method unused_frame: Exchange.DeclareOk response frame

        """
        LOGGER.info('Exchange declared')
        self.setup_queue(self.QUEUE)

    def setup_queue(self, queue_name):
        """Setup the queue on RabbitMQ by invoking the Queue.Declare RPC
        command. When it is complete, the on_queue_declareok method will
        be invoked by pika.

        :param str|unicode queue_name: The name of the queue to declare.

        """
        LOGGER.info('Declaring queue %s', queue_name)
        self._channel.queue_declare(self.on_queue_declareok, queue_name,
                                     arguments={"x-max-priority":20,"x-message-ttl":60000})

    def on_queue_declareok(self, method_frame):
        """Method invoked by pika when the Queue.Declare RPC call made in
        setup_queue has completed. In this method we will bind the queue
        and exchange together with the routing key by issuing the Queue.Bind
        RPC command. When this command is complete, the on_bindok method will
        be invoked by pika.

        :param pika.frame.Method method_frame: The Queue.DeclareOk frame

        """
        LOGGER.info('Binding %s to %s with %s',
                    self.EXCHANGE, self.QUEUE, self.ROUTING_KEY)
        self._channel.queue_bind(self.on_bindok, self.QUEUE,
                                 self.EXCHANGE, self.ROUTING_KEY)

    def on_bindok(self, unused_frame):
        """Invoked by pika when the Queue.Bind method has completed. At this
        point we will start consuming messages by calling start_consuming
        which will invoke the needed RPC commands to start the process.

        :param pika.frame.Method unused_frame: The Queue.BindOk response frame

        """
        LOGGER.info('Queue bound')
        self.start_consuming()

    def start_consuming(self):
        """This method sets up the consumer by first calling
        add_on_cancel_callback so that the object is notified if RabbitMQ
        cancels the consumer. It then issues the Basic.Consume RPC command
        which returns the consumer tag that is used to uniquely identify the
        consumer with RabbitMQ. We keep the value to use it when we want to
        cancel consuming. The on_message method is passed in as a callback pika
        will invoke when a message is fully received.

        """
        LOGGER.info('Issuing consumer related RPC commands')
        self.add_on_cancel_callback()
        self._consumer_tag = self._channel.basic_consume(self.on_message,
                                                         self.QUEUE)

    def add_on_cancel_callback(self):
        """Add a callback that will be invoked if RabbitMQ cancels the consumer
        for some reason. If RabbitMQ does cancel the consumer,
        on_consumer_cancelled will be invoked by pika.

        """
        LOGGER.info('Adding consumer cancellation callback')
        self._channel.add_on_cancel_callback(self.on_consumer_cancelled)

    def on_consumer_cancelled(self, method_frame):
        """Invoked by pika when RabbitMQ sends a Basic.Cancel for a consumer
        receiving messages.

        :param pika.frame.Method method_frame: The Basic.Cancel frame

        """
        LOGGER.info('Consumer was cancelled remotely, shutting down: %r',
                    method_frame)
        if self._channel:
            self._channel.close()

    def on_message(self, unused_channel, basic_deliver, properties, body):
        """Invoked by pika when a message is delivered from RabbitMQ. The
        channel is passed for your convenience. The basic_deliver object that
        is passed in carries the exchange, routing key, delivery tag and
        a redelivered flag for the message. The properties passed in is an
        instance of BasicProperties with the message properties and the body
        is the message that was sent.

        :param pika.channel.Channel unused_channel: The channel object
        :param pika.Spec.Basic.Deliver: basic_deliver method
        :param pika.Spec.BasicProperties: properties
        :param str|unicode body: The message body

        """
        # LOGGER.info('Received message # %s from %s: %s',
        #             basic_deliver.delivery_tag, properties.app_id, body)

        try:
            receive = json.loads(body)
            receive["pika_time"] = time.time()
            self_id = receive["self_id"]
            # print("receving message from {}".format(self_id))
            try:
                # get the bot
                bot = QQBot.objects.get(user_id=self_id)
            except QQBot.DoesNotExist as e:
                LOGGER.error("bot {} does not exsit.".format(self_id))
                raise e
            config = json.load(open(CONFIG_PATH,encoding="utf-8"))
            already_reply = False

            #heart beat
            if(receive["post_type"] == "meta_event" and receive["meta_event_type"] == "heartbeat"):
                LOGGER.debug("bot:{} Event heartbeat at time:{}".format(self_id, int(time.time())))
                call_api(bot, "get_status",{},"get_status:{}".format(self_id))

            if (receive["post_type"] == "message"):
                user_id = receive["user_id"]
                # don't reply another bot
                if(QQBot.objects.filter(user_id=user_id).exists()):
                    raise PikaException("{} reply from another bot:{}".format(receive["self_id"], user_id))

                # replace alter commands
                for (alter_command, command) in handlers.alter_commands.items():
                    if(receive["message"].find(alter_command)==0):
                        receive["message"] = receive["message"].replace(alter_command, command, 1)
                        break
                        
                group_id = None
                group = None
                group_created = False
                #Group Control Func
                if receive["message"].find('\\')==0:
                    receive["message"] = receive["message"].replace('\\', '/', 1)
                if (receive["message_type"]=="group"):
                    group_id = receive["group_id"]
                    (group, group_created) = QQGroup.objects.get_or_create(group_id=group_id)
                    # self-ban in group
                    if(int(time.time()) < group.ban_till):
                        raise PikaException("{} banned by group:{}".format(self_id, group_id))
                        # LOGGER.info("{} banned by group:{}".format(self_id, group_id))
                        # self.acknowledge_message(basic_deliver.delivery_tag)
                        # return
                    group_commands = json.loads(group.commands)

                    try:
                        member_list = json.loads(group.member_list)
                        if group_created or not member_list:
                            update_group_member_list(bot, group_id)
                    except json.decoder.JSONDecodeError:
                        member_list = []
                        
                    
                    if (receive["message"].find('/group_help')==0):
                        msg =  "" if member_list else "本群成员信息获取失败，请尝试重启酷Q并使用/update_group刷新群成员信息\n"
                        for (k, v) in handlers.group_commands.items():
                            msg += "{} : {}\n".format(k,v)
                        msg = msg.strip()
                        send_message(bot, receive["message_type"], group_id or user_id, msg)
                    else:
                        if(receive["message"].find('/update_group')==0):
                            #update_group_member_list(bot, group_id)
                            pass
                        #get sender's user_info
                        user_info = receive["sender"] if "sender" in receive.keys() else None
                        user_info = user_info if (user_info and ("role" in user_info.keys())) else None
                        if member_list and not user_info:
                            for item in member_list:
                                if(int(item["user_id"])==int(user_id)):
                                    user_info = item
                                    break
                        if not user_info:
                            raise PikaException("No user info for user_id:{} in group:{}".format(user_id, group_id))
                            # LOGGER.error("No user info for user_id:{} in group:{}".format(user_id, group_id))
                            # self.acknowledge_message(basic_deliver.delivery_tag)
                            # return

                        group_command_keys = sorted(handlers.group_commands.keys(), key=lambda x:-len(x))
                        for command_key in group_command_keys:
                            if(receive["message"].find(command_key)==0):
                                if receive["message_type"]=="group" and group_commands:
                                    if command_key in group_commands.keys() and group_commands[command_key]=="disable":
                                        continue
                                if not group.registered and command_key!="/group":
                                    msg = "本群%s未在数据库注册，请群主使用/register_group命令注册"%(group_id)
                                    send_message(bot, "group", group_id, msg)
                                    break
                                else:
                                    handle_method = getattr(handlers,"QQGroupCommand_{}".format(command_key.replace("/","",1)))
                                    action_list = handle_method(receive = receive, 
                                                                global_config = config, 
                                                                bot = bot, 
                                                                user_info = user_info, 
                                                                member_list = member_list, 
                                                                group = group,
                                                                commands = handlers.commands,
                                                                group_commands = handlers.group_commands,
                                                                alter_commands = handlers.alter_commands,
                                                                )
                                    for action in action_list:
                                        call_api(bot, action["action"],action["params"],echo=action["echo"])
                                        already_reply = True
                                    if already_reply:
                                        break

                    if not already_reply:
                        action_list = handlers.QQGroupChat(receive = receive, 
                                                            global_config = config, 
                                                            bot = bot, 
                                                            user_info = user_info, 
                                                            member_list = member_list, 
                                                            group = group,
                                                            commands = handlers.commands,
                                                            alter_commands = handlers.alter_commands,
                                                            )
                        for action in action_list:
                            call_api(bot, action["action"],action["params"],echo=action["echo"])
            



                
                

                if (receive["message"].find('/help')==0):
                    msg =  ""
                    for (k, v) in handlers.commands.items():
                        msg += "{} : {}\n".format(k,v)
                    msg += "具体介绍详见Wiki使用手册: {}\n".format("https://github.com/Bluefissure/FFXIVBOT/wiki/")
                    msg = msg.strip()
                    send_message(bot, receive["message_type"], group_id or user_id, msg)

                if (receive["message"].find('/ping')==0):
                    msg =  ""
                    if "detail" in receive["message"]:
                        msg += "[CQ:at,qq={}]\ncoolq->server: {:.2f}s\nserver->rabbitmq: {:.2f}s\nhandle init: {:.2f}s".format(
                            receive["user_id"], 
                            receive["consumer_time"]-receive["time"], 
                            receive["pika_time"]-receive["consumer_time"],
                            time.time()-receive["pika_time"])
                    else:
                        msg += "[CQ:at,qq={}] {:.2f}s".format(receive["user_id"], time.time()-receive["time"])
                    msg = msg.strip()
                    LOGGER.debug("{} calling command: {}".format(user_id, "/ping"))
                    send_message(bot, receive["message_type"], group_id or user_id, msg)

                

                command_keys = sorted(handlers.commands.keys(), key=lambda x:-len(x))
                for command_key in command_keys:
                    if(receive["message"].find(command_key)==0):
                        if receive["message_type"]=="group" and group_commands:
                            if command_key in group_commands.keys() and group_commands[command_key]=="disable":
                                continue
                        LOGGER.debug("{} calling command: {}".format(user_id, command_key))
                        handle_method = getattr(handlers,"QQCommand_{}".format(command_key.replace("/","",1)))
                        action_list = handle_method(receive=receive, global_config=config, bot=bot)
                        # if(len(json.loads(bot.disconnections))>100):
                        #     action_list = self.intercept_action(action_list)
                        for action in action_list:
                            call_api(bot, action["action"],action["params"],echo=action["echo"])
                            already_reply = True
                        break

                
            CONFIG_GROUP_ID = config["CONFIG_GROUP_ID"]
            if (receive["post_type"] == "request"):
                if (receive["request_type"] == "friend"):   #Add Friend
                    qq = receive["user_id"]
                    flag = receive["flag"]
                    if(bot.auto_accept_friend):
                        reply_data = {"flag":flag, "approve": True}
                        call_api(bot, "set_friend_add_request",reply_data)
                if (receive["request_type"] == "group" and receive["sub_type"] == "invite"):    #Invite Group
                    flag = receive["flag"]
                    if(bot.auto_accept_invite):
                        reply_data = {"flag":flag, "sub_type":"invite", "approve": True}
                        call_api(bot, "set_group_add_request",reply_data)
                if (receive["request_type"] == "group" and receive["sub_type"] == "add" and str(receive["group_id"])==CONFIG_GROUP_ID):    #Add Group
                    flag = receive["flag"]
                    user_id = receive["user_id"]
                    qs = QQBot.objects.filter(owner_id=user_id)
                    if(qs.count()>0):
                        reply_data = {"flag":flag, "sub_type":"add", "approve": True}
                        call_api(bot, "set_group_add_request",reply_data)
                        reply_data = {"group_id":CONFIG_GROUP_ID, "user_id":user_id, "special_title":"饲养员"}
                        call_api(bot, "set_group_special_title", reply_data)
            if (receive["post_type"] == "event"):
                if (receive["event"] == "group_increase"):
                    group_id = receive["group_id"]
                    user_id = receive["user_id"]
                    try:
                        group = QQGroup.objects.get(group_id=group_id)
                        msg = group.welcome_msg.strip()
                        if(msg!=""):
                            msg = "[CQ:at,qq=%s]"%(user_id)+msg
                            send_message(bot, "group", group_id, msg)
                    except Exception as e:
                        traceback.print_exc()
            # print(" [x] Received %r" % body)
        except PikaException as pe:
            LOGGER.error(pe)
        except Exception as e:
            LOGGER.error(e)

        self.acknowledge_message(basic_deliver.delivery_tag)

    def acknowledge_message(self, delivery_tag):
        """Acknowledge the message delivery from RabbitMQ by sending a
        Basic.Ack RPC method for the delivery tag.

        :param int delivery_tag: The delivery tag from the Basic.Deliver frame

        """
        LOGGER.info('pid:%s Acknowledging message %s', os.getpid(), delivery_tag)
        self._channel.basic_ack(delivery_tag)

    def stop_consuming(self):
        """Tell RabbitMQ that you would like to stop consuming by sending the
        Basic.Cancel RPC command.

        """
        if self._channel:
            LOGGER.info('Sending a Basic.Cancel RPC command to RabbitMQ')
            self._channel.basic_cancel(self.on_cancelok, self._consumer_tag)

    def on_cancelok(self, unused_frame):
        """This method is invoked by pika when RabbitMQ acknowledges the
        cancellation of a consumer. At this point we will close the channel.
        This will invoke the on_channel_closed method once the channel has been
        closed, which will in-turn close the connection.

        :param pika.frame.Method unused_frame: The Basic.CancelOk frame

        """
        LOGGER.info('RabbitMQ acknowledged the cancellation of the consumer')
        self.close_channel()

    def close_channel(self):
        """Call to close the channel with RabbitMQ cleanly by issuing the
        Channel.Close RPC command.

        """
        LOGGER.info('Closing the channel')
        self._channel.close()

    def run(self):
        """Run the example consumer by connecting to RabbitMQ and then
        starting the IOLoop to block and allow the SelectConnection to operate.

        """
        self._connection = self.connect()
        self._connection.ioloop.start()

    def stop(self):
        """Cleanly shutdown the connection to RabbitMQ by stopping the consumer
        with RabbitMQ. When RabbitMQ confirms the cancellation, on_cancelok
        will be invoked by pika, which will then closing the channel and
        connection. The IOLoop is started again because this method is invoked
        when CTRL-C is pressed raising a KeyboardInterrupt exception. This
        exception stops the IOLoop which needs to be running for pika to
        communicate with RabbitMQ. All of the commands issued prior to starting
        the IOLoop will be buffered but not processed.

        """
        LOGGER.info('Stopping')
        self._closing = True
        self.stop_consuming()
        self._connection.ioloop.start()
        LOGGER.info('Stopped')

    def close_connection(self):
        """This method closes the connection to RabbitMQ."""
        LOGGER.info('Closing connection')
        self._connection.close()


def main():
    # logging.basicConfig(level=logging.INFO, format=LOG_FORMAT)
    logging.basicConfig(level=logging.INFO)
    pikapika = PikaConsumer('amqp://guest:guest@localhost:5672/?heartbeat=600')
    try:
        pikapika.run()
    except KeyboardInterrupt:
        pikapika.stop()


if __name__ == '__main__':
    main()
