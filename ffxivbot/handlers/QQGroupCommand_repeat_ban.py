from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random

class QQGroupCommand_repeat_ban(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQGroupCommand_repeat_ban, self).__init__()
    def __call__(self, **kwargs):
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
            second_command_msg = receive["message"].replace("/repeat_ban","",1).strip()
            second_command = second_command_msg.split(" ")[0].strip()
            if(second_command=="set"):
                if(user_info["role"]!="owner"):
                    msg = "仅群主有权限开启复读机检测系统"
                else:
                    ori_msg = second_command_msg.replace(second_command,"",1).strip()
                    ori_msg = ori_msg.split(' ')
                    if(len(ori_msg)<1):
                        msg = "请设置复读机一分钟内的最大条数（/repeat_ban set $times）"
                    else:
                        if int(ori_msg[0])!=-1:
                            try:
                                group.repeat_ban = max(int(ori_msg[0]),2)
                            except Exception as e:
                                group.repeat_ban = 10
                            group.save()
                            msg = "复读机监控系统已启动，检测值为{}/min".format(group.repeat_ban)
                        else:
                            group.repeat_ban = -1
                            group.save()
                            msg = "复读机监控系统已关闭"
            elif(second_command=="disable"):
                if(user_info["role"]!="owner"):
                    msg = "仅群主有权限关闭复读机检测系统"
                else:
                    group.repeat_ban = -1
                    group.save()
                    msg = "复读机监控系统已关闭"
            else:
                msg = "错误的命令，二级命令有:\"set\", \"disable\""

            reply_action = self.reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)