from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import traceback
import logging
import json
import random
import requests
import math
import string
import os


def QQCommand_bot(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        WEB_BASE_URL = global_config["WEB_BASE_URL"]
        receive = kwargs["receive"]
        bot = kwargs["bot"]
        user_id = receive["user_id"]

        msg = ""
        receive_msg = receive["message"].replace("/bot", "", 1).strip()
        second_command = receive_msg.split(" ")[0]
        second_msg = receive_msg.replace(second_command, "", 1).strip()
        if second_command == "token":
            if receive["message_type"] == "group":
                msg = "[CQ:at,qq={}] 你确定要在群里面申请token从而公之于众？".format(receive["user_id"])
            else:
                (qquser, _) = QQUser.objects.get_or_create(user_id=receive["user_id"])
                qquser.bot_token = second_msg
                qquser.save()
                qquser.refresh_from_db()
                msg = "用户 {} 的token已被设定为：{}".format(qquser, qquser.bot_token)
        elif second_command == "register":
            if receive["message_type"] == "group":
                msg = "[CQ:at,qq={}] 你确定要在群里面申请注册认证码从而公之于众？".format(receive["user_id"])
            else:
                vcode = "".join(
                    random.choices(string.ascii_uppercase + string.digits, k=16)
                )
                (qquser, _) = QQUser.objects.get_or_create(user_id=receive["user_id"])
                qquser.vcode = vcode
                qquser.vcode_time = time.time()
                qquser.save()
                msg = "用户 {} 的注册认证码为：{}".format(qquser, qquser.vcode)
                msg += "\n请在五分钟内访问以下地址进行注册认证："
                msg += os.path.join(
                    WEB_BASE_URL,
                    "register/?vcode={}&email={}@qq.com".format(vcode, qquser),
                )
        elif second_command == "text":
            if int(user_id) != int(bot.owner_id):
                msg = "仅机器人领养者能修改机器人状态"
            else:
                bot.share_banned = not bot.share_banned
                bot.save(update_fields=["share_banned"])
                msg = "文本兼容已{}".format("启用" if bot.share_banned else "禁用")
        elif second_command == "hso":
            if int(user_id) != int(bot.owner_id):
                msg = "仅机器人领养者能修改机器人状态"
            else:
                bot.r18 = not bot.r18
                bot.save(update_fields=["r18"])
                msg = "HSO已{}".format("启用" if bot.r18 else "禁用")
        elif second_command == "api":
            if int(user_id) != int(bot.owner_id):
                msg = "仅机器人领养者能修改机器人状态"
            else:
                bot.api = not bot.api
                bot.save(update_fields=["api"])
                msg = "API已{}".format("启用" if bot.api else "禁用")
        elif second_command == "info":
            friend_list = json.loads(bot.friend_list)
            friend_list_cnt = len(friend_list) if friend_list else 0
            group_list = json.loads(bot.group_list)
            group_list_cnt = len(group_list) if group_list else 0
            reply_api_type = receive.get("reply_api_type", "websocket")
            protocol = reply_api_type
            if reply_api_type == "websocket":
                protocol = "反向Websocket"
            if reply_api_type == "http":
                protocol = "HTTP"
            if reply_api_type == "wechat":
                protocol = "微信"
            if reply_api_type == "tomon":
                protocol = "Tomon Bot"
            if reply_api_type == "iotqq":
                protocol = "OPQBOT(IOTQQ)"
            msg = (
                "姓名：{}\n".format(bot.name)
                + "账号：{}\n".format(bot.user_id)
                + "所在窝：{}\n".format(WEB_BASE_URL.rstrip("/"))
                + "领养者：{}\n".format(bot.owner_id)
                + "链接协议：{}\n".format(protocol)
                + "群数量：{}\n".format(group_list_cnt)
                + "好友数量：{}\n".format(friend_list_cnt)
                + "文本兼容：{}\n".format(bot.share_banned)
                + "HSO: {}\n".format(bot.r18)
                + "API: {}\n".format(bot.api)
            )
            msg = msg.strip()
        elif receive_msg == "update":
            if int(user_id) != int(bot.owner_id):
                msg = "仅机器人领养者能刷新机器人状态"
            else:
                action_list.append(
                    {"action": "get_group_list", "params": {}, "echo": "get_group_list"}
                )
                action_list.append(
                    {
                        "action": "get_friend_list",
                        "params": {"flat": True},
                        "echo": "get_friend_list",
                    }
                )
                action_list.append(
                    {
                        "action": "get_version_info",
                        "params": {},
                        "echo": "get_version_info",
                    }
                )
                msg = "机器人状态统计请求已发送"
        elif receive_msg == "":
            msg = (
                "/bot token $token: 申请接收ACT插件消息时认证的token\n"
                + "/bot update: 更新机器人统计信息\n"
                + "/bot info: 查看机器人信息\n"
                + "/bot register: 申请网站注册认证码\n"
                + "/bot text: 更改连接分享模式\n"
                + "/bot hso: HSO开关\n"
            )
            msg = msg.strip()
        else:
            msg = '无效的二级命令，二级命令有:"token","update","info","register","text","hso","api"'

        msg = msg.strip()
        if msg:
            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
        return action_list
    except Exception as e:
        traceback.print_exc()
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
