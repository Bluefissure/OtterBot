from .QQEventHandler import QQEventHandler
from .QQGroupCommand_sonar import GLOBAL_SONAR_RANKS
from .QQUtils import *
from ffxivbot.models import *
import copy
import traceback
import logging
import json
import random
import requests
import math
import string
import os

def get_server_from_keyword(keyword):
    if keyword == "国服" or keyword == '国':
        return Server.objects.all()
    elif keyword == "陆行鸟" or keyword == '鸟':
        return Server.objects.filter(areaId=1)
    elif keyword == "莫古力" or keyword == '猪':
        return Server.objects.filter(areaId=6)
    elif keyword == "猫小胖" or keyword == '猫':
        return Server.objects.filter(areaId=7)
    elif keyword == "豆豆柴" or keyword == '狗':
        return Server.objects.filter(areaId=8)
    return Server.objects.filter(name=keyword)


def handle_sonar_config(bot, parameters):
    if len(parameters) == 0 or parameters[0] == "help":  # /bot sonar (help)
        return """机器人的 Sonar 推送配置：
/bot sonar info: 查看当前 Sonar 配置
/bot sonar rank/rank_del <50S/60S/70S/80S/90S/100S/大象/小电视/蛇蛇/松鼠>: 添加/删除可通过本机器人推送的上报类别
/bot sonar server/server_del <服务器/大区名称>: 添加/删除可通过本机器人推送的服务器
/bot sonar group/group_del <群号>: 添加/删除可通过本机器人推送的QQ群号（不设置则任意群均不可推送）
"""
    operation = parameters[0]
    if operation == "server" or operation == "server_del":  # /bot sonar server(_del) <keyword>
        for keyword in parameters[1:]:
            servers = get_server_from_keyword(keyword)
            if servers.exists():
                for server in servers:
                    if operation == "server":
                        bot.sonar_sub_servers.add(server)
                    elif operation == "server_del":
                        bot.sonar_sub_servers.remove(server)
        sub_servers = bot.sonar_sub_servers.all()
        if sub_servers.exists():
            servers_msg = "可推送服务器被设置为：\n"
            for server in sub_servers:
                servers_msg += f"{server.name} "
        else:
            servers_msg = "可推送服务器已清空"
        return servers_msg
    if operation == "group" or operation == "group_del":  # /bot sonar group(_del) <group_id>
        for group_id in parameters[1:]:
            groups = QQGroup.objects.filter(group_id=group_id)
            if groups.exists():
                for group in groups:
                    if operation == "group":
                        bot.sonar_sub_groups.add(group)
                    elif operation == "group_del":
                        bot.sonar_sub_groups.remove(group)
        sub_groups = bot.sonar_sub_groups.all()
        if sub_groups.exists():
            groups_msg = "可推送群被设置为：\n"
            for group in sub_groups:
                groups_msg += f"{group} "
        else:
            groups_msg = "可推送群限制已清空"
        return groups_msg
    if operation == "rank" or operation == "rank_del":  # /bot sonar rank(_del) <group_id>
        ranks = json.loads(bot.sonar_sub_ranks)
        for rank in parameters[1:]:
            if rank not in GLOBAL_SONAR_RANKS:
                continue
            if operation == "rank":
                ranks.append(rank)
            elif operation == "rank_del":
                ranks.remove(rank)
        bot.sonar_sub_ranks = json.dumps(ranks)
        bot.save(update_fields=['sonar_sub_ranks'])
        if ranks:
            rank_msg = "可推送类别被设置为：\n"
            for rank in ranks:
                rank_msg += f"{rank} "
        else:
            rank_msg = "可推送类别已清空"
        return rank_msg
    if operation == "info":  # /bot sonar info
        sub_ranks = json.loads(bot.sonar_sub_ranks)
        ranks_msg = ", ".join(list(map(lambda x: str(x), sub_ranks)))
        sub_servers = bot.sonar_sub_servers.all()
        servers_msg = ", ".join(list(map(lambda x: str(x.name), sub_servers)))
        sub_groups = bot.sonar_sub_groups.all()
        groups_msg = ", ".join(list(map(lambda x: str(x.group_id), sub_groups)))
        if groups_msg == "":
            groups_msg = "无"
        return "{} 的 Sonar 推送限制目前设置为：\n" \
                "可推送类别：{}\n" \
                "可推送服务器：{}\n" \
                "可推送群组：{}".format(bot, ranks_msg, servers_msg, groups_msg)
    return "无效命令"
        



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
            (qquser, _) = QQUser.objects.get_or_create(user_id=receive["user_id"])
            vcode = receive_msg.replace("register", "", 1).strip()
            if qquser.vcode and qquser.vcode == vcode:
                qquser.vcode_time = time.time()
            else:
                qquser.vcode_time = 0
            qquser.save(update_fields=["vcode_time"])
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
        elif second_command == "sonar":
            if int(user_id) != int(bot.owner_id):
                msg = "仅机器人领养者能修改机器人状态"
            else:
                parameters = second_msg.split(" ")
                while "" in parameters:
                    parameters.remove("")
                msg = handle_sonar_config(bot, parameters)
        elif second_command == "novelai":
            if int(user_id) != int(bot.owner_id):
                msg = "仅机器人领养者能修改机器人状态"
            else:
                parameters = second_msg.split(" ")
                while "" in parameters:
                    parameters.remove("")
                if parameters[0] == "api":
                    bot.novelai_url = parameters[1]
                    bot.save(update_fields=["novelai_url"])
                    msg = f"{bot} 的 novelai api 已被设定为：{parameters[1]}"
                elif parameters[0] == "group":
                    if parameters[1] == "clear":
                        bot.novelai_groups.clear()
                        msg = f"{bot} 的 novelai group 已被清空"
                    else:
                        group_ids = parameters[1].split(',')
                        for group_id in group_ids:
                            try:
                                group = QQGroup.objects.get(group_id=group_id)
                            except QQGroup.DoesNotExist:
                                continue
                            bot.novelai_groups.add(group)
                        group_str = ", ".join(list(map(lambda x: str(x.group_id), bot.novelai_groups.all())))
                        msg = f"{bot} 的 novelai group 已被设定为：{group_str}"
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
                + "/bot register: 网站注册认证（静默认证）\n"
                + "/bot text: 更改连接分享模式\n"
                + "/bot hso: HSO开关\n"
            )
            msg = msg.strip()
        elif receive_msg.startswith("command"):
            if int(user_id) != int(bot.owner_id):
                msg = "仅机器人领养者能修改机器人状态"
            else:
                COMMAND = copy.deepcopy(kwargs["commands"])
                COMMAND.update(kwargs["group_commands"])
                COMMAND.update(kwargs["alter_commands"])
                COMMAND.update({"/chat": "聊天功能", "/reply": "自定义回复"})
                COMMAND = COMMAND.keys()
                bot_commands = json.loads(bot.commands)
                args = receive_msg.replace("command", "").strip().split(" ")
                while "" in args:
                    args.remove("")
                if len(args) == 0:
                    msg = "请输入命令名称 \"enable /$command\" 或 \"disable /$command\" 或 \"list\""
                elif args[0] == "enable" or args[0] == "disable":
                    command = args[1]
                    if command not in COMMAND:
                        msg = "不存在的命令 \"{}\"".format(command)
                    else:
                        bot_commands[command] = args[0]
                        bot.commands = json.dumps(bot_commands)
                        bot.save(update_fields=["commands"])
                        msg = "命令 \"{}\" 已{}".format(command, "启用" if args[0] == "enable" else "禁用")
                elif args[0] == "list":
                    msg = "命令列表 (未出现命令默认启用)：\n"
                    for (k, v) in bot_commands.items():
                        msg += "{}: {}\n".format(k, v)
        else:
            msg = '无效的二级命令，二级命令有:"token","update","info","register","text","hso","api","command"'

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
