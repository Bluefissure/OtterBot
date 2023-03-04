from .QQEventHandler import QQEventHandler
from .QQUtils import *
from FFXIV import settings
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
import redis
from collections import Counter

def get_tuling_reply(
        request_msg: str,
        token: str,
        userId: str,
        groupId: str,
        TULING_API_URL: str,
    ):
    tuling_data = {}
    tuling_data["reqType"] = 0
    tuling_data["perception"] = {"inputText": {"text": request_msg}}
    tuling_data["userInfo"] = {
        "apiKey": token,
        "userId": userId,
        "groupId": groupId,
    }
    r = requests.post(
        url=TULING_API_URL, data=json.dumps(tuling_data), timeout=3
    )
    tuling_reply = r.json()
    # logging.debug("tuling reply:%s"%(r.text))
    msg = ""
    for item in tuling_reply["results"]:
        if item["resultType"] == "text":
            msg += item["values"]["text"]
    return msg

def get_openai_reply(
        request_msg: str,
        model: str,
        OPENAI_API_KEY: str,
    ):
    openai_data = {
        "model": model,
        "messages": [{
            "role": "user",
            "content": request_msg,
        }]
    }
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {OPENAI_API_KEY}"
    }
    r = requests.post(
        url='https://api.openai.com/v1/chat/completions',
        headers=headers,
        data=json.dumps(openai_data),
        timeout=15
    )
    openai_reply = r.json()
    if "error" in openai_reply:
        print(f"Error handling chatgpt api: {openai_reply['error']['message']}")
        return f"Error: {openai_reply['error']['type']}"
    msg = ""
    for item in openai_reply["choices"]:
        msg += item.get('message', {}).get('content', '') + '\n'
    return msg.strip()



def QQGroupChat(*args, **kwargs):
    try:
        global_config = kwargs.get("global_config", None)
        group = kwargs.get("group", None)
        user_info = kwargs.get("user_info", None)
        TULING_API_URL = global_config.get("TULING_API_URL", None)
        TULING_API_KEY = global_config.get("TULING_API_KEY", None)
        OPENAI_API_KEY = global_config.get("OPENAI_API_KEY", "")
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
        bot_commands = json.loads(bot.commands)

        # custom replys
        reply_enable = check_command_enabled('/reply', bot_commands, group_commands)
        if reply_enable:
            try:
                match_replys = CustomReply.objects.filter(
                    group=group, key=receive["message"].strip().split(" ")[0]
                )
                if match_replys.exists():
                    item = random.choice(match_replys)
                    action_list.append(reply_message_action(receive, item.value))
                    return action_list
            except Exception as e:
                print("received message:{}".format(receive["message"]))
                traceback.print_exc()

        # repeat_ban & repeat
        message = receive["message"].strip()
        r = redis.Redis(host="localhost", port=6379, decode_responses=True)
        message_hash = hashlib.md5(
            (
                message
                + "|{}|{}|{}".format(group.group_id, bot.user_id, settings.SECRET_KEY)
            ).encode()
        ).hexdigest()
        chat = r.get(message_hash) or '{"times":0,"repeated":false}'
        chat_stat = json.loads(chat)
        chat_times = chat_stat["times"] + 1
        chat_repeated = chat_stat["repeated"]
        r.set(
            message_hash,
            json.dumps({"times": chat_times, "repeated": chat_repeated}),
            ex=60,
        )
        if chat_times >= group.repeat_ban > 0:
            msg = "抓到你了，复读姬！╭(╯^╰)╮口球一分钟！"
            if user_info["role"] == "owner":
                msg = "虽然你是狗群主%s无法禁言，但是也触发了复读机检测系统，请闭嘴一分钟[CQ:face,id=14]" % (bot.name)
            if user_info["role"] == "admin":
                msg = "虽然你是狗管理%s无法禁言，但是也触发了复读机检测系统，请闭嘴一分钟[CQ:face,id=14]" % (bot.name)
            msg = "[CQ:at,qq=%s] " % (user_id) + msg
            action_list.append(delete_message_action(receive["message_id"]))
            action_list.append(group_ban_action(group_id, user_id, 60))
            action_list.append(reply_message_action(receive, msg))
        if (
            (not chat_repeated)
            and (not message.startswith("/"))
            and group.repeat_length >= 1
            and group.repeat_prob > 0
            and chat_times >= group.repeat_length
        ):
            if random.randint(1, 100) <= group.repeat_prob:
                action_list.append(reply_message_action(receive, message))
                chat_repeated = True
                r.set(
                    message_hash,
                    json.dumps({"times": chat_times, "repeated": chat_repeated}),
                    ex=60,
                )

        # jieba tokenize and wordcloud
        url_pattern = r"(?:http|https):\/\/((?:[\w-]+)(?:\.[\w-]+)+)(?:[\w.,@?^=%&amp;:\/~+#-]*[\w@?^=%&amp;\/~+#-])?"
        word_pattern = r"^([\u4e00-\u9fff\w]+)$"
        group_id_hash = hashlib.md5(
            ("{}|{}".format(group.group_id, settings.SECRET_KEY)).encode()
        ).hexdigest()
        if group.wordcloud:
            import jieba

            group_mem = r.get(group_id_hash) or "{}"
            group_mem = json.loads(group_mem)
            word_cnt = Counter(group_mem.get("words", {}))
            clear_message = re.sub(r"\[CQ:.*?\]", "", message)
            clear_message = re.sub(url_pattern, "", clear_message)
            word_list = list(
                filter(lambda x: re.match(word_pattern, x), jieba.lcut(clear_message))
            )
            word_cnt.update(Counter(word_list))
            group_mem.update({"words": word_cnt})
            r.set(group_id_hash, json.dumps(group_mem))

        # chatbot
        chat_enable = check_command_enabled('/chat', bot_commands, group_commands)
        at_self_pattern = "\[CQ:at,qq={}(,text=.*)?\]".format(receive["self_id"])
        reply_pattern = "\[CQ:reply,id=.*?\]"
        chatting = re.search(at_self_pattern, receive["message"]) is not None
        wechat = False
        if "self_wechat_id" in receive:
            wechat = True
            mentions = receive["data"]["payload"].get("mention", [])
            chatting = mentions and mentions[0] == receive["self_wechat_id"]
        if chatting and chat_enable:
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
            receive_msg = re.sub(at_self_pattern, "", receive_msg)
            receive_msg = re.sub(reply_pattern, "", receive_msg)
            tuling_token = TULING_API_KEY if bot.tuling_token == "" else bot.tuling_token
            if group.chat_model == 'tuling':
                msg = get_tuling_reply(
                    receive_msg,
                    tuling_token,
                    receive["user_id"] if not wechat else ADMIN_ID,
                    group.group_id,
                    TULING_API_URL,
                )
                if bot.tuling_token == "":
                    msg = msg.replace("图灵工程师爸爸", BOT_FATHER)
                    msg = msg.replace("图灵工程师妈妈", BOT_MOTHER)
                    msg = msg.replace("小主人", USER_NICKNAME)
            elif group.chat_model == 'chatgpt':
                msg = get_openai_reply(
                    receive_msg,
                    'gpt-3.5-turbo',
                    OPENAI_API_KEY,
                )
            else:
                msg = f"不支持的聊天模型：{group.chat_model}"
            msg = re.sub(url_pattern, "http://ff.sdo.com", msg)
            msg = "[CQ:at,qq=%s] " % (receive["user_id"]) + msg
            action = reply_message_action(receive, msg)
            action_list.append(action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        logging.error(e)
    return []
