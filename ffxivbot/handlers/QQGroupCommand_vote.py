from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import time
def QQGroupCommand_vote(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        TIMEFORMAT = global_config["TIMEFORMAT"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]

        msg = "default msg"
        receive_msg = receive["message"].replace('/vote','',1).strip()
        if receive_msg=="list":
            vs = Vote.objects.filter(group=group)
            msg = ""
            for item in vs:
                starttime_str = time.strftime(TIMEFORMAT,time.localtime(item.starttime))
                endtime_str = time.strftime(TIMEFORMAT,time.localtime(item.endtime))
                msg = msg + "#%s:%s %s -- %s\n"%(item.id,item.name,starttime_str,endtime_str)
            msg = msg.strip()
        elif(receive_msg.find("#") == 0):
            receive_msg = receive_msg.replace("#","",1).strip()
            vote_id_str = ""
            for item in receive_msg:
                if(str.isdigit(item)):
                    vote_id_str += item
                else:
                    break
            vote_id = int(vote_id_str) if vote_id_str!="" else 0
            votes = Vote.objects.filter(id=vote_id,group=group)
            if(len(votes)==0):
                msg = "不存在#%s号投票"%(vote_id)
            else:
                receive_msg = receive_msg.replace(vote_id_str,"",1).strip()
                if(receive_msg.find("check")==0 or receive_msg==""):
                    vote = votes[0]
                    vote_json = json.loads(vote.vote)
                    sum_list = [{"qq":item[0],"tot":len(item[1]["voted_by"])} for item in vote_json.items()]
                    sum_list.sort(key=lambda x: x["tot"],reverse=True)
                    msg = "#%s:%s目前票数:\n"%(vote.id,vote.name)
                    for item in sum_list:
                        msg += "[CQ:at,qq=%s] : %s\n"%(item["qq"],item["tot"])
                else:
                    pattern = "[CQ:at,qq="
                    qq_str = receive_msg
                    qq = qq_str
                    if(qq_str.find(pattern)>=0):
                        qq = qq_str[qq_str.find(pattern)+len(pattern):qq_str.find("]")]
                    if (not qq.isdecimal()):
                        msg = "请艾特某人进行投票"
                    else:
                        vote = votes[0]
                        if(time.time()<vote.starttime):
                            msg = "投票 #%s:%s 未开始。"%(vote.id,vote.name)
                        else:
                            if(time.time()>vote.endtime):
                                msg = "投票 #%s:%s 已结束。"%(vote.id,vote.name)
                            else:
                                vote_json = json.loads(vote.vote)
                                can_vote = True
                                for (k,v) in vote_json.items():
                                    if(str(user_id) in v["voted_by"]):
                                        msg = "[CQ:at,qq=%s] 在 #%s:%s 中已投票，不可重复投票。"%(user_id,vote.id,vote.name)
                                        break
                                else:
                                    if(str(qq) not in vote_json.keys()):
                                        vote_json[str(qq)] = {
                                            "voted_by":[str(user_id)]
                                        }
                                    vote_list = vote_json[str(qq)]["voted_by"]
                                    vote_list.append(str(user_id))
                                    vote_list = list(set(vote_list))
                                    vote_json[str(qq)]["voted_by"] = vote_list
                                    vote.vote = json.dumps(vote_json)
                                    vote.save()
                                    msg = "[CQ:at,qq=%s] 在 #%s:%s 中给 [CQ:at,qq=%s] 投票成功，目前票数%s。"%(user_id,vote.id,vote.name,qq,len(vote_list))
        else:
            msg = "/vote list: 群内投票ID与内容\n/vote #$id check : 投票$id的目前结果\n/vote #$id @$member : 通过艾特给某人投票"
        msg = msg.strip()

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)