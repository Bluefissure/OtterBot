from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

def QQGroupCommand_revenge(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]

        msg = "default msg"
        second_command_msg = receive["message"].replace("/revenge","",1).strip()
        second_command = second_command_msg.split(" ")[0].strip()
        revs = Revenge.objects.filter(user_id=user_id,group=group,timestamp__gt=time.time()-3600)
        del_revs = Revenge.objects.filter(timestamp__lt=time.time()-3600)
        for item in del_revs:
            item.delete()
        if(second_command==""):
            if(len(revs)>0):
                rev = revs[0]
                qq_list = (json.loads(rev.vote_list))["voted_by"]
                msg = "[CQ:at,qq=%s] 将要与"%(user_id)
                for item in qq_list:
                    msg += "[CQ:at,qq=%s] "%(item)
                msg += "展开复仇,您将被禁言%s分钟,其余众人将被禁言%s分钟，确认请发送/revenge confirm"%(int(rev.ban_time)*(len(qq_list)),rev.ban_time)
            else:
                msg = "不存在关于您的复仇机会。"
        elif(second_command=="confirm"):
            if(len(revs)>0):
                rev = revs[0]
                qq_list = (json.loads(rev.vote_list))["voted_by"]
                for item in qq_list:
                    if(str(item)==str(user_id)):
                        continue
                    ban_action = group_ban_action(group_id,item,int(rev.ban_time)*60)
                    action_list.append(ban_action)
                ban_action = group_ban_action(group_id,user_id,int(rev.ban_time)*(len(qq_list))*60)
                action_list.append(ban_action)
                msg = "[CQ:at,qq=%s] 复仇完毕，嘻嘻嘻。"%(user_id)
                rev.delete()
            else:
                msg = "不存在关于您的复仇机会。"
        else:
            msg = "错误的命令，二级命令有:\"confirm\""
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)