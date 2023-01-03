from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging

def QQCommand_raid(*args, **kwargs):
    action_list = []
    try:
        receive = kwargs["receive"]
        msg = "default message"
        receive_msg = receive["message"]
        receive_msg = receive_msg.replace("/raid", "", 1).strip()
        args = receive_msg.split(" ")
        if len(args) < 2:
            msg = "参数格式错误：/raid 角色名 服务器"
        else:
            wol_name = args[0].strip()
            server_name = args[1].strip()
            server = None
            servers = Server.objects.all()
            for s in servers:
                if server_name in str(s.name) or server_name in str(s.alter_names):
                    server = s
            if not server:
                msg = "未找到服务器：{}".format(server_name)
            else:
                msg = ""
                data = {
                    "method": "queryhreodata",
                    "stage": 6,
                    "name": wol_name,
                    "areaId": server.areaId,
                    "groupId": server.groupId,
                }
                msg += check_raid(
                    api_url="https://actff1.web.sdo.com/20180525HeroList/Server/HeroList190128.ashx",
                    raid_data=data,
                    raid_name="万魔殿炼净之狱",
                    wol_name=wol_name,
                    server_name=server.name,
                )
                # data["stage"] = 3
                # msg += check_raid(
                #     api_url="https://actff1.web.sdo.com/20180525HeroList/Server/HeroList190128.ashx",
                #     raid_data=data,
                #     raid_name="共鸣之章",
                #     wol_name=wol_name,
                #     server_name=server.name,
                # )
                # data["stage"] = 4
                # msg += check_raid(
                #     api_url="https://actff1.web.sdo.com/20180525HeroList/Server/HeroList190128.ashx",
                #     raid_data=data,
                #     raid_name="再生之章",
                #     wol_name=wol_name,
                #     server_name=server.name,
                # )
                msg = msg.strip()

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
