from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import hashlib
from bs4 import BeautifulSoup
import traceback
import re
import time


def QQGroupChat(*args, **kwargs):
    try:
        global_config = kwargs.get("global_config", None)
        group = kwargs.get("group", None)
        user_info = kwargs.get("user_info", None)
        QQ_BASE_URL = global_config.get("QQ_BASE_URL", None)
        TULING_API_URL = global_config.get("TULING_API_URL", None)
        TULING_API_KEY = global_config.get("TULING_API_KEY", None)
        ADMIN_ID = global_config.get("ADMIN_ID", "")
        BOT_FATHER = global_config.get("BOT_FATHER", None)
        BOT_MOTHER = global_config.get("BOT_MOTHER", None)
        USER_NICKNAME = global_config.get("USER_NICKNAME", "小暗呆")
        action_list = []
        receive = kwargs["receive"]
        bot = kwargs["bot"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]
        group_commands = json.loads(group.commands)

        #custom replys
        reply_enable = group_commands.get("/reply", "enable") != "disable"
        if reply_enable:
            try:
                match_replys = CustomReply.objects.filter(group=group,key=receive["message"].strip().split(" ")[0])
                if(match_replys.exists()):
                    item = random.choice(match_replys)
                    action_list.append(reply_message_action(receive, item.value))
                    return action_list
            except Exception as e:
                print("received message:{}".format(receive["message"]))
                traceback.print_exc()
        
        #repeat_ban & repeat
        message = receive["message"].strip()
        message_hash = hashlib.md5((message+"|{}".format(bot.user_id)).encode()).hexdigest()
        chats = ChatMessage.objects.filter(group=group, message_hash=message_hash).filter(timestamp__gt=int(time.time())-60)
        if(chats.exists()):
            chat = chats[0]
            chat.message = message
            chat.timestamp = int(time.time())
            chat.times = chat.times + 1
            chat.save(update_fields=["timestamp", "times", "message"])
            if(group.repeat_ban>0 and chat.times>=group.repeat_ban):
                msg = "抓到你了，复读姬！╭(╯^╰)╮口球一分钟！"
                if(user_info["role"]=="owner"):
                    msg = "虽然你是狗群主%s无法禁言，但是也触发了复读机检测系统，请闭嘴一分钟[CQ:face,id=14]"%(bot.name)
                if(user_info["role"]=="admin"):
                    msg = "虽然你是狗管理%s无法禁言，但是也触发了复读机检测系统，请闭嘴一分钟[CQ:face,id=14]"%(bot.name)
                msg = "[CQ:at,qq=%s] "%(user_id) + msg
                action_list.append(delete_message_action(receive["message_id"]))
                action_list.append(group_ban_action(group_id, user_id, 60))
                action_list.append(reply_message_action(receive, msg))
            if((not message.startswith("/")) and group.repeat_length>=1 and group.repeat_prob>0 and chat.times>=group.repeat_length and (not chat.repeated)):
                if(random.randint(1, 100) <= group.repeat_prob):
                    # logging.error("repeat reply with bot:{} message:{}".format(bot.user_id, chat.message))
                    action_list.append(reply_message_action(receive, chat.message))
                    chat.repeated = True
                    chat.save(update_fields=["repeated"])
        else:
            if(group.repeat_ban>0 or (group.repeat_length>=1 and group.repeat_prob>0) ):
                if(receive["self_id"]!=receive["user_id"]):
                    # print("creating new chat message:{}".format(message))
                    chat = ChatMessage(group=group,timestamp=time.time(),message_hash=message_hash)
                    chat.save()

        #tuling chatbot
        chat_enable = group_commands.get("/chat", "enable") != "disable"
        chatting = "[CQ:at,qq=%s]"%(receive["self_id"]) in receive["message"]
        wechat = False
        if "self_wechat_id" in receive:
            wechat = True
            mentions = receive["data"]["payload"].get("mention", [])
            chatting = mentions and mentions[0] == receive["self_wechat_id"]
            print("mentions:{} chatting:{}".format(mentions, chatting))
        if(chatting and chat_enable):
            user = QQUser.objects.filter(user_id=user_id)
            if user.exists():
                user = user.first()
                if user.last_chat_time + 5 > time.time():
                    msg = "聊天太频繁啦！獭獭脑子转不过来了！！"
                    action = reply_message_action(receive, msg)
                    action_list.append(action)
                    return action_list
                user.last_chat_time = time.time()
                user.save(update_fields=["last_chat_time"])
            receive_msg = message
            receive_msg = receive_msg.replace("[CQ:at,qq=%s]"%(receive["self_id"]),"")
            tuling_data = {}
            tuling_data["reqType"] = 0 
            tuling_data["perception"] = {"inputText": {"text": receive_msg}}
            tuling_data["userInfo"] = {"apiKey": TULING_API_KEY if bot.tuling_token=="" else bot.tuling_token,
                                         "userId": receive["user_id"] if not wechat else ADMIN_ID, 
                                         "groupId": group.group_id
                                         }
            r = requests.post(url=TULING_API_URL,data=json.dumps(tuling_data),timeout=3)
            tuling_reply = r.json()
            # logging.debug("tuling reply:%s"%(r.text))
            msg = ""
            for item in tuling_reply["results"]:
                if(item["resultType"]=="text"):
                    msg += item["values"]["text"]
            if bot.tuling_token=="":
                msg = msg.replace("图灵工程师爸爸", BOT_FATHER)
                msg = msg.replace("图灵工程师妈妈", BOT_MOTHER)
                msg = msg.replace("小主人", USER_NICKNAME)
            msg = re.sub(r"(?:http|https):\/\/((?:[\w-]+)(?:\.[\w-]+)+)(?:[\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?", "http://ff.sdo.com", msg)
            msg = "[CQ:at,qq=%s] "%(receive["user_id"])+msg
            action = reply_message_action(receive, msg)
            action_list.append(action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        logging.error(e)
    return []
