from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random

def QQGroupCommand_ban(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        member_list = kwargs["member_list"]
        bot = kwargs["bot"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]

        msg = "default msg"
        second_command_msg = receive["message"].replace("/ban","",1).strip()
        second_command = second_command_msg.split(" ")[0].strip()
        if(second_command=="" or second_command=="help"):
            msg = "/ban $user $time: 给$user开启时长为$time分钟的禁言投票\n/ban $user: 给$user的禁言投票+1"
        elif(second_command=="set"):
            if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                msg = "仅群主与管理员有权限设置禁言投票"
            else:
                ban_cnt = second_command_msg.replace(second_command,"",1).strip()
                try:
                    group.ban_cnt = max(int(ban_cnt),2)
                    if(int(ban_cnt)==-1):
                        group.ban_cnt = -1
                except:
                    group.ban_cnt = 10
                group.save()
                msg = "禁言投票基准被设置为{}".format(group.ban_cnt)
                if(group.ban_cnt==-1):
                    msg = "禁言投票已关闭"
        else:
            if(group.ban_cnt<=0):
                msg = "本群未开放禁言投票功能"
            else:
                receive_msg = second_command_msg.strip()
                msg_list = receive_msg.split(' ')
                while('' in msg_list):
                    msg_list.remove('')
                # print(msg_list)
                if(len(msg_list)>=1):
                    pattern = "[CQ:at,qq="
                    qq_str = msg_list[0]
                    if(qq_str.find(pattern)>=0):
                        qq = qq_str[qq_str.find(pattern)+len(pattern):qq_str.find("]")]
                    else:
                        qq = qq_str
                    if not qq.isdecimal():
                        msg = "请艾特某人或输入其QQ号码"
                    else:
                        mems = BanMember.objects.filter(user_id=qq,group=group,timestamp__gt=time.time()-3600)
                        del_mems = BanMember.objects.filter(user_id=qq,group=group,timestamp__lt=time.time()-3600)
                        for item in del_mems:
                            item.delete()
                        if(len(msg_list)==1):
                            if(len(mems)==0):
                                msg = "不存在针对 [CQ:at,qq=%s] 的禁言投票，请输入\"/ban %s $time\"开始时长为$time分钟的禁言投票"%(qq,qq)
                            else:
                                mem = mems[0]
                                vtlist = json.loads(mem.vote_list)
                                if("voted_by" not in vtlist.keys()):
                                    vtlist["voted_by"] = []
                                vtlist["voted_by"].append(str(receive["user_id"]))
                                vtlist["voted_by"] = list(set(vtlist["voted_by"]))
                                mem.vote_list = json.dumps(vtlist)
                                mem.save()
                                if(len(vtlist["voted_by"]) >= group.ban_cnt):
                                    target_user_info = None
                                    for item in member_list:
                                        if(int(item["user_id"])==int(qq)):
                                            target_user_info = item
                                            break
                                    if not target_user_info:
                                        msg = "未找到%s成员信息"%(target_user_info)
                                        target_user_info = {"role":"member"}
                                    voted_msg = ""
                                    for item in vtlist["voted_by"]:
                                        voted_msg += "[CQ:at,qq=%s] "%(item)
                                    msg = "[CQ:at,qq=%s] 被%s投票禁言%s分钟"%(qq, voted_msg, mem.ban_time)
                                    msg += " 复仇请输入/revenge"
                                    if(target_user_info["role"]=="owner"):
                                        msg = "[CQ:at,qq=%s] 虽然你是狗群主%s无法禁言，但是也被群友投票禁言，请闭嘴%s分钟[CQ:face,id=14]"%(qq, bot.name, mem.ban_time)
                                    if(target_user_info["role"]=="admin"):
                                        msg = "[CQ:at,qq=%s] 虽然你是狗管理%s无法禁言，但是也被群友投票禁言，请闭嘴%s分钟[CQ:face,id=14]"%(qq, bot.name, mem.ban_time)
                                    if(str(mem.user_id) == str(receive["self_id"])):
                                        msg = "%s竟然禁言了可爱的%s[CQ:face,id=111][CQ:face,id=111]好吧我闭嘴%s分钟[CQ:face,id=14]"%(voted_msg, bot.name, mem.ban_time)
                                        group.ban_till = time.time()+int(mem.ban_time)*60
                                        group.save()
                                    else:
                                        ban_action = group_ban_action(group_id,qq,int(mem.ban_time)*60)
                                        action_list.append(ban_action)
                                        rev = Revenge(user_id=mem.user_id,group=group)
                                        rev.timestamp = time.time()
                                        rev.vote_list = mem.vote_list
                                        rev.ban_time = mem.ban_time
                                        rev.save()
                                    mem.delete()
                                else:
                                    msg = "[CQ:at,qq=%s] 时长为%s分钟的禁言投票，目前进度：%s/%s"%(mem.user_id,mem.ban_time,len(vtlist["voted_by"]),group.ban_cnt)

                        elif(len(msg_list)==2):
                            if not msg_list[1].isdecimal():
                                msg = "禁言时长无效"
                            else:
                                if(len(mems)==0):
                                    max_ban_time = 10
                                    ban_time = min(int(msg_list[1]),max_ban_time) if int(qq)!=int(receive["self_id"]) else int(msg_list[1])
                                    mem = BanMember(user_id=qq,group=group,ban_time=ban_time)
                                    vtlist = json.loads(mem.vote_list)
                                    vtlist["voted_by"] = []
                                    vtlist["voted_by"].append(str(receive["user_id"]))
                                    vtlist["voted_by"] = list(set(vtlist["voted_by"]))
                                    mem.vote_list = json.dumps(vtlist)
                                    mem.timestamp = time.time()
                                    mem.save()
                                    msg = "开始了针对 [CQ:at,qq=%s] 时长为%s分钟的禁言投票，投票请发送/ban %s"%(qq,mem.ban_time,qq)
                                else:
                                    mem = mems[0]
                                    msg = "已存在针对 [CQ:at,qq=%s] 时长为%s分钟的禁言投票，投票请发送/ban %s"%(qq,mem.ban_time,qq)
            

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
