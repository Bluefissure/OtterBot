from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import traceback
from bs4 import BeautifulSoup


def QQGroupCommand_live(*args, **kwargs):
    action_list = []
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
        second_command_msg = receive["message"].replace("/live","",1).strip()
        param_segs = second_command_msg.split(" ")
        while "" in param_segs:
            param_segs.remove("")
        try:
            optype = param_segs[0].strip()
        except IndexError:
            optype = "help"
        if(optype=="add"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                msg = "仅群主与管理员有权限设置直播订阅"
            else:
                try:
                    platform = param_segs[1].strip()
                    room = param_segs[2].strip()
                    if platform not in ["bilibili", "douyu"]:
                        msg = "目前不支持平台\"{}\"，请检查输入。".format(platform)
                    else:
                        (lvu, lvu_created) = LiveUser.objects.get_or_create(room_id=int(room), platform=platform)
                        if lvu_created:
                            # lvu.save()
                            # group.live_subscription.add(lvu)
                            msg = "功能升级中，暂时无法新增直播订阅"
                        else:
                            group.live_subscription.add(lvu)
                            msg = "{} 的订阅添加成功".format(lvu)
                # except LiveUser.DoesNotExist:
                #     msg = "未设置 {} 的订阅计划，请检查输入或联系机器人管理员添加".format(live_name)
                except IndexError:
                    msg = "参数个数错误，请检查命令"
        elif(optype=="del"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                msg = "仅群主与管理员有权限设置直播订阅"
            else:
                try:
                    platform = param_segs[1].strip()
                    room = param_segs[2].strip()
                    if platform not in ["bilibili", "douyu"]:
                        msg = "目前不支持平台\"{}\"，请检查输入。".format(platform)
                    else:
                        lvu = LiveUser.objects.get(room_id=int(room), platform=platform)
                        group.live_subscription.remove(lvu)
                        msg = "{} 的订阅删除成功".format(lvu)
                except LiveUser.DoesNotExist:
                    msg = "没有找到 {} 的订阅，请检查输入或联系机器人管理员".format(live_name)
                except IndexError:
                    msg = "参数个数错误，请检查命令"
        elif(optype=="list"):
            lvus = group.live_subscription.all()
            msg = "本群订阅的主播有：\n"
            for lvu in lvus:
                msg += "{}\n".format(lvu)
            msg = msg.strip()
        else:
            msg = "/live add $platform $room: 添加$platform平台的$room房间订阅\n" + \
                    "/live del $platform $room: 删除$platform平台的$room房间订阅\n" + \
                    "/live list: 列出当前的群内订阅"
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc(e)
    return action_list