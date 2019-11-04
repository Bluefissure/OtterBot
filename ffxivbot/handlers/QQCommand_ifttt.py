from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
from django.db.models import Q
from html import unescape
import traceback
import logging
import json
import random
import requests
import math
import time
import re

def get_image_from_CQ(CQ_text):
    if "url=" in CQ_text:
        tmp = CQ_text
        tmp = tmp[tmp.find("url=") : -1]
        tmp = tmp.replace("url=", "")
        img_url = tmp.replace("]", "")
        return img_url
    return ""

def QQCommand_ifttt(*args, **kwargs):
    action_list = []
    receive = kwargs["receive"]
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        TIMEFORMAT_YMDHMS = global_config["TIMEFORMAT"]
        bot = kwargs["bot"]
        user_id = receive["user_id"]
        msg = ""
        receive_msg = receive["message"].replace("/ifttt", "", 1).strip()
        second_command = receive_msg.split(" ")[0]
        second_msg = receive_msg.replace(second_command, "", 1).strip()
        if second_command == "token":
            if receive["message_type"] == "group":
                msg = "[CQ:at,qq={}] 你确定要在群里面设置token从而公之于众？".format(receive["user_id"])
            else:
                (qquser, created) = QQUser.objects.get_or_create(
                    user_id=receive["user_id"]
                )
                qquser.ifttt_token = second_msg
                qquser.save()
                msg = "用户 {} 的 IFTTT Token 已被设定为：\"{}\"".format(qquser, qquser.ifttt_token)
        elif second_command == "info":
            try:
                assert receive["message_type"] == "group", "仅在群内才可使用 /ifttt info 命令"
                group = QQGroup.objects.get(group_id = int(receive["group_id"]))
                ifttt_channel = IFTTTChannel.objects.get(group = group)
                msg = "IFTTT频道信息如下：\n频道名称:\"{}\"\n频道人数:{}\n上次推送:{}".format(
                    ifttt_channel.name, 
                    ifttt_channel.members.count(),
                    time.strftime(TIMEFORMAT_YMDHMS, time.localtime(ifttt_channel.last_push_time))
                    )
            except AssertionError as e:
                msg = str(e)
            except QQGroup.DoesNotExist as e:
                msg = "本群未注册，请群主使用/group register命令注册"
            except IFTTTChannel.DoesNotExist as e:
                msg = "本群未注册IFTTT频道，请群主或管理员使用/ifttt register $name命令注册"
        elif second_command == "push":
            try:
                assert receive["message_type"] == "group", "仅在群内才可使用 /ifttt info 命令"
                group = QQGroup.objects.get(group_id = int(receive["group_id"]))
                member_list = json.loads(group.member_list)
                assert user_id in [item["user_id"] for item in member_list if (item["role"]=="owner" or item["role"]=="admin")], \
                    "仅群主与管理员有权限发送IFTTT推送"
                ifttt_channel = IFTTTChannel.objects.get(group = group)
                to_push_members = ifttt_channel.members.filter(~Q(ifttt_token=""))
                img_url = get_image_from_CQ(second_msg)
                if img_url:
                    second_msg = re.sub(r'\[CQ:image,.*?\]', '', second_msg)
                success_cnt, fail_cnt = 0, 0
                for user in to_push_members:
                    url = "https://maker.ifttt.com/trigger/ffxivbot_rich/with/key/{}".format(user.ifttt_token)
                    json_data = {
                        "value1": second_msg,
                        "value2": unescape(ifttt_channel.callback_link),
                        "value3": img_url
                    }
                    r = requests.post(url, json=json_data)
                    if r.status_code == 200:
                        success_cnt += 1
                    else:
                        fail_cnt += 1
                    if success_cnt > 0:
                        ifttt_channel.last_push_time = int(time.time())
                        ifttt_channel.save(update_fields=["last_push_time"])
                msg = "IFTTT频道推送消息成功{}条，失败{}条".format(success_cnt, fail_cnt)
            except AssertionError as e:
                msg = str(e)
            except QQGroup.DoesNotExist as e:
                msg = "本群未注册，请群主使用/group register命令注册"
            except IFTTTChannel.DoesNotExist as e:
                msg = "本群未注册IFTTT频道，请群主或管理员使用/ifttt register $name命令注册"
        elif second_command == "callback_link":
            try:
                assert receive["message_type"] == "group", "仅在群内才可使用 /ifttt callback_link 命令"
                group = QQGroup.objects.get(group_id = int(receive["group_id"]))
                member_list = json.loads(group.member_list)
                assert user_id in [item["user_id"] for item in member_list if (item["role"]=="owner" or item["role"]=="admin")], \
                    "仅群主与管理员有权限管理IFTTT频道"
                ifttt_channel = IFTTTChannel.objects.get(group = group)
                ifttt_channel.callback_link = second_msg
                ifttt_channel.save()
                msg = "IFTTT频道\"{}\"已更新回调地址为：{}".format(ifttt_channel.name, ifttt_channel.callback_link)
            except AssertionError as e:
                msg = str(e)
            except QQGroup.DoesNotExist as e:
                msg = "本群未注册，请群主使用/group register命令注册"
            except IFTTTChannel.DoesNotExist as e:
                msg = "本群未注册IFTTT频道，请群主或管理员使用/ifttt register $name命令注册"
        elif second_command == "register":
            try:
                assert receive["message_type"] == "group", "仅在群内才可使用 /ifttt register 命令"
                group = QQGroup.objects.get(group_id = int(receive["group_id"]))
                member_list = json.loads(group.member_list)
                assert user_id in [item["user_id"] for item in member_list if (item["role"]=="owner" or item["role"]=="admin")], \
                    "仅群主与管理员有权限注册IFTTT频道"
                (ifttt_channel, created) = IFTTTChannel.objects.get_or_create(group = group)
                ifttt_channel.members.all().delete()    # remove all former members
                ifttt_channel.name = second_msg
                for ppl in member_list:
                    (qquser, created) = QQUser.objects.get_or_create(
                        user_id=ppl["user_id"]
                    )
                    ifttt_channel.members.add(qquser)
                ifttt_channel.save()
                msg = "IFTTT频道\"{}\"已创建成功，并自动添加了本群内的{}名用户为听众".format(ifttt_channel.name, ifttt_channel.members.count())
            except AssertionError as e:
                msg = str(e)
            except QQGroup.DoesNotExist as e:
                msg = "本群未注册，请群主使用/group register命令注册"
        elif second_command == "":
            msg = (
                "/ifttt info: 查看IFTTT频道信息\n"+\
                "/ifttt push $msg: 推送消息$msg到本群的IFTTT频道\n"+\
                "/ifttt callback_link $link: 设定推送消息的回调连接地址（建议设置为群邀请URL）\n"+\
                "/ifttt register $name: 注册本群IFTTT频道\n"+\
                "/ifttt token $token: 提供接收IFTTT消息时认证的Token\n"
            )
            msg = msg.strip()
        else:
            msg = '无效的二级命令，二级命令有:"info","register","token"'

        msg = msg.strip()
        if msg:
            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        traceback.print_exc()
        logging.error(e)
    return action_list
