from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random
import requests

class QQCommand_raid(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_raid, self).__init__()
    def __call__(self, **kwargs):
        try:
            QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]

            msg = "default message"
            receive_msg = receive["message"]
            receive_msg = receive_msg.replace("/raid","",1).strip()
            args = receive_msg.split(" ")
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
                    "method":"queryhreodata",
                    "name":wol_name,
                    "areaId":server.areaId,
                    'groupId':server.groupId,
                    }
                r = requests.post(url="http://act.ff.sdo.com/20180525HeroList/Server/HeroList171213.ashx",data=data)
                res = json.loads(r.text)
                if(int(res["Code"])!=0):
                    msg += res["Message"]
                else:
                    if res["Attach"]["Level1"]:
                        msg += "{}--{} 的 西格玛幻境 挑战情况如下：\n".format(server.name, wol_name)
                        for i in range(4):
                            l = i+1
                            level = "Level{}".format(l)
                            raid_name = "西格玛幻境"
                            if res["Attach"][level]:
                                if len(res["Attach"][level].strip())==8:
                                    date = res["Attach"][level]
                                    fdate = "{}-{}-{}".format(date[:4],date[4:6],date[6:8])
                                    msg += "{}{}: {}\n".format(raid_name, l, fdate)
                                else:
                                    msg += "{}{}: 数据缺失\n".format(raid_name, l)

                            else:
                                msg += "{}{} : 仍未攻破\n".format(raid_name, l)
                    else:
                        msg += "{}--{} 还没有突破过任何零式德尔塔幻境，请继续努力哦~\n".format(server.name, wol_name)

                r = requests.post(url="http://act.ff.sdo.com/20171213HeroList/Server/HeroList171213.ashx",data=data)
                res = json.loads(r.text)
                if(int(res["Code"])!=0):
                    msg += res["Message"]
                else:
                    if res["Attach"]["Level1"]:
                        msg += "{}--{} 的 德尔塔幻境 挑战情况如下：\n".format(server.name, wol_name)
                        for i in range(4):
                            l = i+1
                            level = "Level{}".format(l)
                            raid_name = "德尔塔幻境"
                            if res["Attach"][level]:
                                if len(res["Attach"][level].strip())==8:
                                    date = res["Attach"][level]
                                    fdate = "{}-{}-{}".format(date[:4],date[4:6],date[6:8])
                                    msg += "{}{}: {}\n".format(raid_name, l, fdate)
                                else:
                                    msg += "{}{}: 数据缺失\n".format(raid_name, l)

                            else:
                                msg += "{}{} : 仍未攻破\n".format(raid_name, l)
                    else:
                        msg += "{}--{} 还没有突破过任何零式德尔塔幻境，请继续努力哦~\n".format(server.name, wol_name)

                msg = msg.strip()

            reply_action = self.reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)
