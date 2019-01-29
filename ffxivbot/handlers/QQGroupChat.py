from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
from bs4 import BeautifulSoup
import traceback


def QQGroupChat(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        TULING_API_URL = global_config["TULING_API_URL"]
        TULING_API_KEY = global_config["TULING_API_KEY"]
        BOT_FATHER = global_config["BOT_FATHER"]
        BOT_MOTHER = global_config["BOT_MOTHER"]
        USER_NICKNAME = global_config["USER_NICKNAME"]
        action_list = []
        receive = kwargs["receive"]
        bot = kwargs["bot"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]
        group_commands = json.loads(group.commands)

        
        #custom replys
        reply_enable = False if("/reply" in group_commands.keys() and group_commands["/reply"]=="disable") else True
        if reply_enable:
            try:
                match_replys = CustomReply.objects.filter(group=group,key=receive["message"].strip().split(" ")[0])
                if(match_replys.exists()):
                    item = match_replys[random.randint(0,len(match_replys)-1)]
                    msg = item.value
                    msg_action = reply_message_action(receive, msg)
                    action_list.append(msg_action)
                    return action_list
            except Exception as e:
                print("received message:{}".format(receive["message"]))
                traceback.print_exc()
        
        #repeat_ban & repeat
        chats = ChatMessage.objects.filter(group=group,timestamp__gt=time.time()-60,message=receive["message"].strip())
        if(chats.exists()):
            chat = chats[0]
            chat.timestamp = int(time.time())
            chat.times = chat.times+1
            chat.save(update_fields=["timestamp", "times"])
            if(group.repeat_ban>0 and chat.times>=group.repeat_ban):
                msg = "抓到你了，复读姬！╭(╯^╰)╮口球一分钟！"
                if(user_info["role"]=="owner"):
                    msg = "虽然你是狗群主%s无法禁言，但是也触发了复读机检测系统，请闭嘴一分钟[CQ:face,id=14]"%(bot.name)
                if(user_info["role"]=="admin"):
                    msg = "虽然你是狗管理%s无法禁言，但是也触发了复读机检测系统，请闭嘴一分钟[CQ:face,id=14]"%(bot.name)
                msg = "[CQ:at,qq=%s] "%(user_id) + msg
                action = delete_message_action(receive["message_id"])
                action_list.append(action)
                action = group_ban_action(group_id, user_id, 60)
                action_list.append(action)
                action = reply_message_action(receive, msg)
                action_list.append(action)
            if(group.repeat_length>=1 and group.repeat_prob>0 and chat.times>=group.repeat_length and (not chat.repeated)):
                if(random.randint(1,100)<=group.repeat_prob):
                    action = reply_message_action(receive, chat.message)
                    action_list.append(action)
                    chat.repeated = True
                    chat.save(update_fields=["repeated"])
        else:
            if(group.repeat_ban>0 or (group.repeat_length>=1 and group.repeat_prob>0) ):
                if(receive["self_id"]!=receive["user_id"]):
                    chat = ChatMessage(group=group,message=receive["message"].strip(),timestamp=time.time())
                    chat.save()

        #fudai
        if("收到福袋，请使用新版手机QQ查看" in receive["message"] and group.antifukubukuro):
            print("福袋iiiiiiiiiiiii")
            action = delete_message_action(receive["message_id"])
            action_list.append(action)



        #weibo subscription
        wbus = group.subscription.all()
        for wbu in wbus:
            wbts = wbu.tile.all()
            for wbt in wbts:
                if group not in wbt.pushed_group.all():
                    wbt.pushed_group.add(group)
                    wbt.save()
                    res_data = get_weibotile_share(wbt)
                    tmp_msg = [{"type":"share","data":res_data}]
                    if(wbt.crawled_time>=int(time.time())-group.subscription_trigger_time):
                        action = reply_message_action(receive, tmp_msg)
                        action_list.append(action)
                    break

        #tuling chatbot
        chat_enable = False if("/chat" in group_commands.keys() and group_commands["/chat"]=="disable") else True
        if("[CQ:at,qq=%s]"%(receive["self_id"]) in receive["message"] and chat_enable):
            if(group.left_reply_cnt <= 0):
                msg = "聊天限额已耗尽，请等待回复。"
            else:
                logging.debug("Tuling reply")
                receive_msg = receive["message"]
                receive_msg = receive_msg.replace("[CQ:at,qq=%s]"%(receive["self_id"]),"")
                tuling_data = {}
                tuling_data["reqType"] = 0  #Text
                tuling_data["perception"] = {"inputText": {"text": receive_msg}}
                tuling_data["userInfo"] = {"apiKey": TULING_API_KEY if bot.tuling_token=="" else bot.tuling_token,
                                             "userId": receive["user_id"], 
                                             "groupId": group.group_id
                                             }
                r = requests.post(url=TULING_API_URL,data=json.dumps(tuling_data),timeout=3)
                tuling_reply = json.loads(r.text)
                logging.debug("tuling reply:%s"%(r.text))
                tuling_results = tuling_reply["results"]
                msg = ""
                for item in tuling_results:
                    if(item["resultType"]=="text"):
                        msg += item["values"]["text"]
                if bot.tuling_token=="":
                    msg = msg.replace("图灵工程师爸爸",BOT_FATHER)
                    msg = msg.replace("图灵工程师妈妈",BOT_MOTHER)
                    msg = msg.replace("小主人",USER_NICKNAME)
                group.left_reply_cnt = max(group.left_reply_cnt - 1, 0)
                group.save(update_fields=["left_reply_cnt"])
                msg = "[CQ:at,qq=%s] "%(receive["user_id"])+msg
            action = reply_message_action(receive, msg)
            action_list.append(action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        logging.error(e)
    return []