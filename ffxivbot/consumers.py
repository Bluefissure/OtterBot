from channels.generic.websocket import WebsocketConsumer
from channels.layers import get_channel_layer 
from django.db import transaction
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


CONFIG_PATH = "/home/ubuntu/FFXIVBOT/ffxivbot/config.json"
GLOBAL_EVENT_HANDLE = True

class APIConsumer(WebsocketConsumer):
    @transaction.atomic 
    def connect(self):
        header_list = self.scope["headers"]
        headers = {}
        for (k,v) in header_list:
            headers[k.decode()] = v.decode()
        ws_self_id = headers['x-self-id']
        ws_client_role = headers['x-client-role']
        ws_access_token = headers['authorization'].replace("Token","").strip()
        bots = QQBot.objects.select_for_update().filter(user_id=ws_self_id,access_token=ws_access_token)
        if(len(bots) == 0):
            logging.error("%s:%s:API:AUTH_FAIL"%(ws_self_id, ws_access_token))
            self.close()
            return
        if(len(bots) > 1):
            logging.error("%s:%s:API:MULTIPLE_AUTH"%(ws_self_id, ws_access_token))
            self.close()
            return
        self.bot = bots[0]
        self.bot_user_id = self.bot.user_id
        self.bot.api_channel_name = self.channel_name
        self.bot.api_time = int(time.time())
        logging.debug("New API Connection:%s"%(self.channel_name))
        self.bot.save()
        logging.debug("API Channel connect from {} by channel:{}".format(self.bot.user_id,self.bot.api_channel_name))
        self.accept()

    def disconnect(self, close_code):
        try:
            logging.debug("API Channel disconnect from {} by channel:{}".format(self.bot.user_id,self.bot.api_channel_name))
        except:
            pass
    @transaction.atomic 
    def receive(self, text_data):
        # print("API Channel received from {} channel:{}".format(self.bot.user_id,self.bot.api_channel_name))
        self.bot = QQBot.objects.select_for_update().get(user_id=self.bot_user_id)
        self.bot.api_time = int(time.time())
        self.bot.api_channel_name = self.channel_name
        receive = json.loads(text_data)
        if(int(receive["retcode"])!=0):
            if (int(receive["retcode"])==1 and receive["status"]=="async"):
                logging.warning("API waring:"+text_data)
            else:
                logging.error("API error:"+text_data)
        # print("API receive:{}".format(receive))
        if("echo" in receive.keys()):
            echo = receive["echo"]
            logging.debug("echo:{} received".format(receive["echo"]))
            if(echo.find("get_group_member_list")==0):
                group_id = echo.replace("get_group_member_list:","").strip()
                groups = QQGroup.objects.select_for_update().filter(group_id=group_id)
                if(len(groups)>0):
                    group = groups[0]
                    group.member_list = json.dumps(receive["data"]) if receive["data"] else "[]"
                    logging.debug("group %s member updated"%(group.group_id))
                    group.save()
            if(echo.find("get_group_list")==0):
                # group_list = echo.replace("get_group_list:","").strip()
                self.bot.group_list = json.dumps(receive["data"])
            if(echo.find("_get_friend_list")==0):
                # friend_list = echo.replace("_get_friend_list:","").strip()
                self.bot.friend_list = json.dumps(receive["data"])
            if(echo.find("get_version_info")==0):
                self.bot.version_info = json.dumps(receive["data"])
            if(echo.find("get_status")==0):
                user_id = echo.split(":")[1]
                if(not receive["data"] or not receive["data"]["good"]):
                    logging.error("bot:{} offline at time:{}".format(user_id, int(time.time())))
        self.bot.save()

    def send_event(self, event):
        logging.debug("APIChannel {} send_event with event:{}".format(self.channel_name, json.dumps(event)))
        self.send(text_data=event["text"])



class EventConsumer(WebsocketConsumer):
    @transaction.atomic
    def connect(self):
        header_list = self.scope["headers"]
        headers = {}
        for (k,v) in header_list:
            headers[k.decode()] = v.decode()
        ws_self_id = headers['x-self-id']
        ws_client_role = headers['x-client-role']
        ws_access_token = headers['authorization'].replace("Token","").strip()
        bots = QQBot.objects.select_for_update().filter(user_id=ws_self_id,access_token=ws_access_token)
        if(len(bots) == 0):
            logging.error("%s:%s:Event:AUTH_FAIL"%(ws_self_id, ws_access_token))
            return
        if(len(bots) > 1):
            logging.error("%s:%s:Event:MULTIPLE_AUTH"%(ws_self_id, ws_access_token))
            return
        self.bot = bots[0]
        self.bot_user_id = self.bot.user_id
        self.bot.event_channel_name = self.channel_name
        self.bot.event_time = int(time.time())
        self.bot.save()
        logging.debug("Event Channel connect from {} by channel:{}".format(self.bot.user_id,self.bot.event_channel_name))
        self.accept()

    def disconnect(self, close_code):
        try:
            logging.debug("Event Channel disconnect from {} by channel:{}".format(self.bot.user_id,self.bot.event_channel_name))
        except:
            pass

    def call_api(self, action, params, echo=None):
        if("async" not in action and not echo):
            action = action + "_async"
        jdata = {
            "action":action,
            "params":params,
        }
        if echo:
            jdata["echo"] = echo
        self.bot.refresh_from_db()
        if(self.bot.api_channel_name == ""):
            logging.error("empty channel for bot:{}".format(self.bot.user_id))
            return
        # channel_layer.send(self.bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})
        async_to_sync(channel_layer.send)(self.bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})

    def call_event(self, action, params, echo=None):
        if("async" not in action and echo is None):
            action = action + "_async"
        jdata = {
            "action":action,
            "params":params,
        }
        if echo:
            jdata["echo"] = echo
        self.bot.refresh_from_db()
        if(self.bot.event_channel_name == ""):
            logging.error("empty channel for bot:{}".format(self.bot.user_id))
            return
        # channel_layer.send(self.bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})
        async_to_sync(channel_layer.send)(self.bot.event_channel_name, {"type": "send.event","text": json.dumps(jdata),})

    def send_message(self, private_group, uid, message):
        if(private_group=="group"):
            self.call_api("send_group_msg",{"group_id":uid,"message":message})
        if(private_group=="private"):
            self.call_api("send_private_msg",{"user_id":uid,"message":message})


    def send_event(self, event):
        logging.debug("EventChannel {} send_event with event:{}".format(self.channel_name, event))
        self.send(text_data=event["text"])

    def update_group_member_list(self,group_id):
        self.call_api("get_group_member_list",{"group_id":group_id},"get_group_member_list:%s"%(group_id))

    def delete_message(self, message_id):
        self.call_api("delete_msg",{"message_id":message_id})


    def group_ban(self,group_id,user_id,duration):
        json_data = {"group_id":group_id,"user_id":user_id,"duration":duration}
        self.call_api("set_group_ban",json_data)

    @transaction.atomic
    def receive(self, text_data):
        # print("Event Channel receive from {} by channel:{}".format(self.bot.user_id,self.bot.event_channel_name))
        self.bot = QQBot.objects.select_for_update().get(user_id=self.bot_user_id)
        self.bot.event_time = int(time.time())
        # if(int(time.time()) > self.bot.api_time+60):
        #     self.call_api("get_status",{},"get_status:{}".format(self.bot_user_id))
        self.bot.event_channel_name = self.channel_name
        self.config = json.load(open(CONFIG_PATH,encoding="utf-8"))

        #print("received Event message:"+text_data)
        global GLOBAL_EVENT_HANDLE
        if(GLOBAL_EVENT_HANDLE):
            try:
                receive = json.loads(text_data)
                if (receive["post_type"] == "message"):
                    # Self-ban in group
                    user_id = receive["user_id"]
                    group_id = None
                    group = None
                    if (receive["message_type"]=="group"):
                        group_id = receive["group_id"]
                        group_list = QQGroup.objects.filter(group_id=group_id)
                        if len(group_list)>0:
                            group = group_list[0]
                            if(int(time.time())<group.ban_till):
                                return
                            group_bots = json.loads(group.bots)
                            if(user_id in group_bots):
                                return
                            group_commands = json.loads(group.commands)



                    if (receive["message"].find('/help')==0):
                        msg =  ""
                        for (k, v) in handlers.commands.items():
                            msg += "{} : {}\n".format(k,v)
                        msg = msg.strip()
                        self.send_message(receive["message_type"], group_id or user_id, msg)

                    for (alter_command, command) in handlers.alter_commands.items():
                        if(receive["message"].find(alter_command)==0):
                            receive["message"] = receive["message"].replace(alter_command, command, 1)

                    command_keys = sorted(handlers.commands.keys())
                    command_keys.reverse()
                    for command_key in command_keys:
                        if(receive["message"].find(command_key)==0):
                            if receive["message_type"]=="group" and group_commands:
                                if command_key in group_commands.keys() and group_commands[command_key]=="disable":
                                    continue
                            handle_module = eval("handlers.QQCommand_{}()".format(command_key.replace("/","",1)))
                            action_list = handle_module(receive=receive, global_config=self.config, bot=self.bot)
                            for action in action_list:
                                self.call_api(action["action"],action["params"],echo=action["echo"])
                            break

                    #Group Control Func
                    if (receive["message_type"]=="group"):
                        (group, group_created) = QQGroup.objects.get_or_create(group_id=group_id)
                        group_commands = json.loads(group.commands)
                        try:
                            member_list = json.loads(group.member_list)
                            if group_created or not member_list:
                                self.update_group_member_list(group_id)
                                time.sleep(1)
                                group.refresh_from_db()
                                member_list = json.loads(group.member_list)
                        except:
                            self.update_group_member_list(group_id)
                            member_list = []
                            
                        
                        if (receive["message"].find('/group_help')==0):
                            msg =  "" if member_list else "本群成员信息获取失败，请尝试重启酷Q并使用/update_group刷新群成员信息"
                            for (k, v) in handlers.group_commands.items():
                                msg += "{} : {}\n".format(k,v)
                            msg = msg.strip()
                            self.send_message(receive["message_type"], group_id or user_id, msg)
                        else:
                            if(receive["message"].find('/update_group')==0 or not member_list):
                                self.update_group_member_list(group_id)
                            #get sender's user_info
                            if not group:
                                logging.warning("No group:{}".format(group_id))
                                return
                            if not member_list:
                                logging.warning("No member info for group:{}".format(group_id))
                                return
                            user_info = None
                            for item in member_list:
                                if(int(item["user_id"])==int(user_id)):
                                    user_info = item
                                    break
                            if not user_info:
                                logging.debug("No user info for user_id:{} in group:{}".format(user_id,group_id))
                                return

                            group_command_keys = sorted(handlers.group_commands.keys())
                            group_command_keys.reverse()
                            for command_key in group_command_keys:
                                if(receive["message"].find(command_key)==0):
                                    if receive["message_type"]=="group" and group_commands:
                                        if command_key in group_commands.keys() and group_commands[command_key]=="disable":
                                            continue
                                    if not group.registered and command_key!="/group":
                                        msg = "本群%s未在数据库注册，请群主使用/register_group命令注册"%(group_id)
                                        self.send_message("group", group_id, msg)
                                        break
                                    else:
                                        handle_module = eval("handlers.QQGroupCommand_{}()".format(command_key.replace("/","",1)))
                                        action_list = handle_module(receive = receive, 
                                                                    global_config = self.config, 
                                                                    bot = self.bot, 
                                                                    user_info = user_info, 
                                                                    member_list = member_list, 
                                                                    group = group,
                                                                    commands = handlers.commands,
                                                                    group_commands = handlers.group_commands,
                                                                    )
                                        for action in action_list:
                                            self.call_api(action["action"],action["params"],echo=action["echo"])
                                        break

                        general_chat_handler = handlers.QQGroupChat()
                        action_list = general_chat_handler(receive = receive, 
                                                            global_config = self.config, 
                                                            bot = self.bot, 
                                                            user_info = user_info, 
                                                            member_list = member_list, 
                                                            group = group,
                                                            commands = handlers.commands,
                                                            group_commands = handlers.group_commands,
                                                            )
                        for action in action_list:
                            self.call_api(action["action"],action["params"],echo=action["echo"])
                


                CONFIG_GROUP_ID = self.config["CONFIG_GROUP_ID"]
                if (receive["post_type"] == "request"):
                    if (receive["request_type"] == "friend"):   #Add Friend
                        qq = receive["user_id"]
                        flag = receive["flag"]
                        if(self.bot.auto_accept_friend):
                            reply_data = {"flag":flag, "approve": True}
                            self.call_api("set_friend_add_request",reply_data)
                    if (receive["request_type"] == "group" and receive["sub_type"] == "invite"):    #Invite Group
                        flag = receive["flag"]
                        if(self.bot.auto_accept_invite):
                            reply_data = {"flag":flag, "sub_type":"invite", "approve": True}
                            self.call_api("set_group_add_request",reply_data)
                    if (receive["request_type"] == "group" and receive["sub_type"] == "add" and str(receive["group_id"])==CONFIG_GROUP_ID):    #Add Group
                        flag = receive["flag"]
                        user_id = receive["user_id"]
                        qs = QQBot.objects.filter(owner_id=user_id)
                        if(len(qs)>0):
                            reply_data = {"flag":flag, "sub_type":"add", "approve": True}
                            self.call_api("set_group_add_request",reply_data)
                            time.sleep(1)
                            reply_data = {"group_id":CONFIG_GROUP_ID, "user_id":user_id, "special_title":"饲养员"}
                            self.call_api("set_group_special_title", reply_data)
                if (receive["post_type"] == "event"):
                    if (receive["event"] == "group_increase"):
                        group_id = receive["group_id"]
                        user_id = receive["user_id"]
                        group_list = QQGroup.objects.filter(group_id=group_id)
                        if len(group_list)>0:
                            group = group_list[0]
                            msg = group.welcome_msg.strip()
                            if(msg!=""):
                                msg = "[CQ:at,qq=%s]"%(user_id)+msg
                                self.send_message("group", group_id, msg)
            except Exception as e:
                traceback.print_exc() 
        self.bot.save()
class WSConsumer(WebsocketConsumer):
    def connect(self):
        pass
    def disconnect(self, close_code):
        pass
    def receive(self, text_data):
        pass
