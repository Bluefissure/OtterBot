from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import html
import traceback
from collections import Counter  

def QQGroupCommand_custom_reply(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]
        msg = "default msg"
        second_command_msg = receive["message"].replace("/custom_reply","",1).strip()
        segs = second_command_msg.split(" ")
        while "" in segs:
            segs.remove("")
        second_command = segs[0].strip()
        if(second_command=="add"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                msg = "仅群主与管理员有权限设置自定义回复"
            else:
                custom_key = segs[1].strip()
                if(custom_key[0]!='/'):
                    msg = "自定义命令以'/'开头"
                else:
                    custom_value = html.unescape(" ".join(segs[2:]))
                    custom = CustomReply(group=group,key=custom_key,value=custom_value)
                    custom.save()
                    msg = "自定义回复已添加成功，使用\"{}\"查看".format(custom_key)
        elif(second_command=="del"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                msg = "仅群主与管理员有权限设置自定义回复"
            else:
                custom_key = segs[1].strip()
                customs = CustomReply.objects.filter(group=group,key=custom_key)
                for item in customs:
                    item.delete()
                msg = "自定义回复\"{}\"已删除".format(custom_key)
        elif(second_command=="list"):
            counter = Counter()
            msg = "目前群内的自定义回复有：\n"
            replys = CustomReply.objects.filter(group=group)
            for reply in replys:
                counter[reply.key] += 1
            for key, cnt in counter.items():
                msg += "{}*{}\n".format(key, cnt) if cnt > 1 else "{}\n".format(key)
            msg = msg.strip()
        else:
            msg = "错误的命令，二级命令有:\"add\", \"del\", \"list\""

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        traceback.print_exc() 
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        return action_list