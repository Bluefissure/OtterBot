from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

GLOBAL_SONAR_RANKS = [
    "50S", "60S", "70S", "80S", "90S",
    "大象", "小电视", "海呱", "地呱", "雷马", "玉藻御前", "夜光花", "长须豹女王", "贝希摩斯", "奥丁"
]

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


def handle_sonar_config(group, parameters):
    group_bots = json.loads(group.bots)
    if not group_bots:
        return "本群未设置上报机器人，请通过 /group bot <机器人QQ> 添加。（多个机器人取第一个）"
    bot_id = group_bots[0]
    try:
        bot = QQBot.objects.get(user_id=bot_id)
    except QQBot.DoesNotExist:
        return f"推送机器人 {bot_id} 不存在。"

    bot_all_groups = bot.sonar_sub_groups.all()
    if not bot.sonar_sub_groups.filter(group_id=group.group_id).exists():
        return f"本群不具备机器人 {bot_id} 的推送资格，请联系领养者设置。"

    if len(parameters) == 0 or parameters[0] == "help":  # /sonar (help)
        return """本群的 Sonar 推送配置：
/sonar info: 查看本群当前 Sonar 配置
/sonar rank/rank_del <50S/60S/70S/80S/90S/大象/小电视/...>: 添加/删除推送的上报类别
/sonar server/server_del <服务器/大区名称>: 添加/删推送的服务器
"""

    operation = parameters[0]
    if operation == "server" or operation == "server_del":  # /sonar server(_del) <keyword>
        for keyword in parameters[1:]:
            servers = get_server_from_keyword(keyword)
            if servers.exists():
                for server in servers:
                    if operation == "server" and bot.sonar_sub_servers.filter(id=server.id).exists():
                        group.sonar_sub_servers.add(server)
                    elif operation == "server_del":
                        group.sonar_sub_servers.remove(server)
        sub_servers = group.sonar_sub_servers.all()
        if sub_servers.exists():
            servers_msg = "本群推送服务器被设置为：\n"
            for server in sub_servers:
                servers_msg += f"{server.name} "
        else:
            servers_msg = "本群推送服务器已清空"
        return servers_msg
    if operation == "rank" or operation == "rank_del":  # /sonar rank(_del) <group_id>
        ranks = json.loads(group.sonar_sub_ranks)
        bot_ranks = json.loads(bot.sonar_sub_ranks)
        for rank in parameters[1:]:
            if rank not in GLOBAL_SONAR_RANKS:
                continue
            if operation == "rank" and rank in bot_ranks:
                if rank not in ranks:
                    ranks.append(rank)
            elif operation == "rank_del":
                while rank in ranks:
                    ranks.remove(rank)
        group.sonar_sub_ranks = json.dumps(ranks)
        group.save(update_fields=['sonar_sub_ranks'])
        if ranks:
            rank_msg = "本群推送类别被设置为：\n"
            for rank in ranks:
                rank_msg += f"{rank} "
        else:
            rank_msg = "本群推送类别已清空"
        return rank_msg
    if operation == "info":  # /sonar info
        sub_ranks = json.loads(group.sonar_sub_ranks)
        ranks_msg = ", ".join(list(map(lambda x: str(x), sub_ranks)))
        sub_servers = group.sonar_sub_servers.all()
        servers_msg = ", ".join(list(map(lambda x: str(x.name), sub_servers)))
        return "{} 的 Sonar 推送目前设置为：\n" \
                "类别：{}\n" \
                "服务器：{}".format(group.group_id, ranks_msg, servers_msg)
    return "无效命令"
        

def QQGroupCommand_sonar(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        action_list = []
        receive = kwargs["receive"]

        user_id = receive["user_id"]
        group_id = receive["group_id"]
        msg = "default msg"
        second_command_msg = receive["message"].replace("/sonar", "", 1).strip()
        parameters = second_command_msg.split(" ")
        while "" in parameters:
            parameters.remove("")
        if user_info["role"] != "owner":
            msg = "仅群主有权限设置群 Sonar 推送"
        else:
            msg = handle_sonar_config(group, parameters)

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return []
