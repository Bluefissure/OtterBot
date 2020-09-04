from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
from bs4 import BeautifulSoup


def get_weibotile_share(weibotile):
    content_json = json.loads(weibotile.content)
    mblog = content_json["mblog"]
    bs = BeautifulSoup(mblog["text"],"lxml")
    res_data = {
        "url":content_json["scheme"],
        "title":bs.get_text().replace("\u200b","")[:32],
        "content":"From {}\'s Weibo".format(weibotile.owner),
        "image":mblog["user"]["profile_image_url"],
    }
    logging.debug("weibo_share")
    logging.debug(json.dumps(res_data))
    return res_data

def QQGroupCommand_weibo(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]

        msg = "default msg"
        second_command_msg = receive["message"].replace("/weibo","",1).strip()
        second_command = second_command_msg.split(" ")[0].strip()
        if(second_command=="add"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                msg = "仅群主与管理员有权限设置微博订阅"
            else:
                weibo_name = second_command_msg.replace('add','',1).strip()
                wbus = WeiboUser.objects.filter(name=weibo_name)
                if(len(wbus)==0):
                    msg = "未设置 {} 的订阅计划，请联系机器人管理员添加".format(weibo_name)
                else:
                    wbu = wbus[0]
                    group.subscription.add(wbu)
                    group.save()
                    msg = "{} 的订阅添加成功".format(weibo_name)
                    wts = wbu.tile.all().order_by("-crawled_time")
                    for wt in wts:
                        wt.pushed_group.add(group)
                    if(len(wts)>0):
                        wt = wts[0]
                        res_data = get_weibotile_share(wt)
                        tmp_msg = [{"type":"share","data":res_data}]
                        msg_action = reply_message_action(receive, tmp_msg)
                        action_list.append(msg_action)
        elif(second_command=="del"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                msg = "仅群主与管理员有权限设置微博订阅"
            else:
                weibo_name = second_command_msg.replace('del','',1).strip()
                wbus = WeiboUser.objects.filter(name=weibo_name)
                if(len(wbus)==0):
                    msg = "未设置 {} 的订阅计划，请联系机器人管理员添加".format(weibo_name)
                else:
                    wbu = wbus[0]
                    group.subscription.remove(wbu)
                    group.save()
                    msg = "{} 的订阅删除成功".format(weibo_name)
        elif(second_command=="list"):
            wbus = group.subscription.all()
            msg = "本群订阅的微博用户有：\n"
            for wbu in wbus:
                msg += "{}\n".format(wbu)
            msg = msg.strip()
        else:
            msg = "错误的命令，二级命令有:\"add\", \"del\", \"list\""

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)