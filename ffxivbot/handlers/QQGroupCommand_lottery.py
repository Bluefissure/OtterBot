from django.db.models import Q
from django.db import DatabaseError, transaction
from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import requests_cache
import math
import re
import traceback
import uuid
import time


@transaction.atomic
def QQGroupCommand_lottery(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        RANDOMORG_TOKEN = global_config.get("RANDOMORG_TOKEN", None)
        TIMEFORMAT = global_config["TIMEFORMAT"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]

        msg = "未能匹配的命令，请阅读使用说明或联系开发者排查。"
        receive_msg = receive["message"].replace('/lottery','',1).strip()
        receive_segs = list(filter(lambda x: x != "", receive_msg.split(" ")))
        if len(receive_segs)==0 or receive_segs[0].find("help")==0:
            msg = "/lottery create $name: 添加名为$name的抽奖\
\n/lottery #$id halt: 终止$id号抽奖\
\n/lottery #$id user add/del $user: 给$id号抽奖添加/删除参与者$user(需要@)\
\n/lottery #$id prize add/del $prize: 给$id号抽奖添加/删除奖品$prize\
\n/lottery #$id public: 将$id号抽奖公开化，群内所有人均可注册\
\n/lottery #$id register: 注册参与$id号抽奖\
\n/lottery #$id info: 输出$id号抽奖的信息\
\n/lottery #$id finish: 结束$id号抽奖，返回抽奖结果\
\n/lottery #$id verify: 确认$id号抽奖结果无黑幕"
        else:
            command = receive_segs[0]
            if command == "create":
                try:
                    lottery_name = receive_segs[1]
                except IndexError:
                    msg = "缺少参数，请检查命令格式"
                else:
                    lotts = Lottery.objects.filter(group=group)
                    running_lotts = lotts.filter(end_time=0)
                    if running_lotts.exists():
                        msg = "群内有仍未结束的抽奖，请结束后再创建新的抽奖："
                        for lott in running_lotts:
                            msg += "\n#{}: {} by [CQ:at,qq={}]".format(lott.id, lott.name, lott.host_user)
                        msg += "\n创建者和管理员可以通过\"/lottery #id halt\"来终止抽奖"
                    else:
                        lott = Lottery(name=lottery_name, host_user=user_id, group=group)
                        lott.uuid = uuid.uuid4()
                        lott.begin_time = time.time()
                        lott.save()
                        msg = "抽奖\"#{}: {}\"添加成功".format(lott.id, lott.name)
            elif command.find("#")==0:
                lottery_id = receive_segs[0].replace("#","")
                try:
                    lottery_id = int(lottery_id)
                    lott = Lottery.objects.select_for_update().get(group=group, id=lottery_id)
                except ValueError:
                    msg = "抽奖ID无效:\"{}\"".format(lottery_id)
                except Lottery.DoesNotExist:
                    msg = "不存在#{}的抽奖".format(lottery_id)
                else:
                    sec_command = receive_segs[1]
                    if sec_command == "info":
                        msg = lott.info(TIMEFORMAT = TIMEFORMAT)
                    elif sec_command=="halt":
                        try:
                            assert lott.host_user==str(user_id) or user_info["role"]=="admin" or user_info["role"]=="owner", "您不是抽奖组织者或管理员，无权更改抽奖信息"
                            assert lott.end_time==0, "抽奖已结束"
                        except AssertionError as e:
                            msg = str(e)
                        else:
                            lott.end_time = int(time.time())
                            lott.save(update_fields=["end_time"])
                            msg = "抽奖\"#{}: {}\"已于{}强行终止".format(lott.id, lott.name, time.strftime(TIMEFORMAT,time.localtime(lott.end_time)))
                    elif sec_command=="prize":
                        try:
                            prize_command = receive_segs[2]
                            prize_name = receive_segs[3]
                            assert lott.host_user==str(user_id), "您不是抽奖组织者，无权更改抽奖信息"
                            assert lott.end_time==0, "抽奖已结束"
                        except IndexError:
                            msg = "缺少参数，请检查命令格式"
                        except AssertionError as e:
                            msg = str(e)
                        else:
                            prize_num = 1
                            try:
                                if "*" in prize_name:
                                    prize_name, prize_num = prize_name.split("*")
                                    prize_num = int(prize_num)
                            except ValueError:
                                prize_num = 1
                                pass
                            prizes = json.loads(lott.prize)
                            if prize_command=="add":
                                for i in range(prize_num):
                                    prizes.append(prize_name)
                            elif prize_command=="del":
                                for i in range(prize_num):
                                    prizes.remove(prize_name)
                            lott.prize = json.dumps(prizes)
                            lott.save(update_fields=["prize"])
                            msg = "抽奖\"#{}: {}\"奖品信息已更新：\n{}".format(lott.id, lott.name, lott.prize_info())
                    elif sec_command=="user":
                        try:
                            user_command = receive_segs[2]
                            user_name = receive_segs[3]
                            assert lott.host_user==str(user_id), "您不是抽奖组织者，无权更改抽奖信息"
                            assert lott.end_time==0, "抽奖已结束"
                        except IndexError:
                            msg = "缺少参数，请检查命令格式"
                        except AssertionError as e:
                            msg = str(e)
                        else:
                            members = json.loads(lott.participate_user)
                            mem_list = re.findall("\[CQ:at,qq=(\d+)\]",user_name)
                            if len(mem_list)==0:
                                msg = "没有匹配用户信息，请确认您艾特成功"
                            else:
                                if user_command=="add":
                                    for qq in mem_list:
                                        if str(qq) not in members:
                                            members.append(str(qq))
                                elif user_command=="del":
                                    for qq in mem_list:
                                        members.remove(str(qq))
                                lott.participate_user = json.dumps(members)
                                lott.save(update_fields=["participate_user"])
                                msg = "{} 已成功报名抽奖\"#{}: {}\"".format(" ".join(["[CQ:at,qq={}]".format(qq) for qq in mem_list]), lott.id, lott.name)
                    elif sec_command=="public":
                        try:
                            assert lott.host_user==str(user_id), "您不是抽奖组织者，无权更改抽奖信息"
                            assert lott.end_time==0, "抽奖已结束"
                        except AssertionError as e:
                            msg = str(e)
                        else:
                            lott.public = True
                            lott.save(update_fields=["public"])
                            msg = "抽奖\"#{}: {}\"已变更为可公开注册模式".format(lott.id, lott.name)
                    elif sec_command=="register":
                        try:
                            assert lott.public, "抽奖\"#{}: {}\"非公开可注册状态，无法报名".format( lott.id, lott.name)
                            assert lott.end_time==0, "抽奖已结束"
                        except AssertionError as e:
                            msg = str(e)
                        else:
                            members = json.loads(lott.participate_user)
                            if str(user_id) in members:
                                msg = "[CQ:at,qq={}] 请不要重复报名".format(user_id)
                            else:
                                members.append(str(user_id))
                                lott.participate_user = json.dumps(members)
                                lott.save(update_fields=["participate_user"])
                                msg = "[CQ:at,qq={}] 您已报名抽奖\"#{}: {}\"".format(user_id, lott.id, lott.name)
                    elif sec_command=="finish":
                        try:
                            assert lott.host_user==str(user_id), "您不是抽奖组织者，无权更改抽奖信息"
                            assert lott.end_time==0, "抽奖已结束，无法重复抽奖"
                            assert lott.mode==1, "目前只支持random.org模式的随机发生器"
                        except AssertionError as e:
                            msg = str(e)
                        else:
                            msg = lott.info(TIMEFORMAT = TIMEFORMAT)
                            msg += "\n如果确认以该条件抽奖，请输入\"/lottery #{} finish_confirm\"".format(lott.id)
                    elif sec_command=="finish_confirm":
                        try:
                            assert lott.host_user==str(user_id), "您不是抽奖组织者，无权更改抽奖信息"
                            assert lott.end_time==0, "抽奖已结束，无法重复抽奖"
                            assert lott.mode==1, "目前只支持random.org模式的随机发生器"
                            assert len(json.loads(lott.prize))>=1, "奖品为空，无法进行抽奖"
                            if lott.mode==1:
                                assert RANDOMORG_TOKEN, "未提供random.org的API Token"
                        except AssertionError as e:
                            msg = str(e)
                        else:
                            members = json.loads(lott.participate_user)
                            prizes = json.loads(lott.prize)
                            req_json = {
                                "jsonrpc": "2.0",
                                "method": "generateSignedIntegers",
                                "params": {
                                    "apiKey": RANDOMORG_TOKEN,
                                    "n": len(members),
                                    "min": 1,
                                    "max": len(members),
                                    "replacement": False
                                },
                                "id": lott.id
                            }
                            with requests_cache.disabled(): #disable cache
                                r = requests.post(url="https://api.random.org/json-rpc/2/invoke", json=req_json)
                                if r.status_code==200:
                                    res_json = r.json()
                                    if "error" in res_json.keys():
                                        msg = "API Error: {}\n{}".format(res_json["error"]["code"], res_json["error"]["message"])
                                    else:
                                        lott.random_res = json.dumps(res_json)
                                        lott.end_time = int(time.time())
                                        lott.save(update_fields=["random_res","end_time"])
                                        msg = "抽奖结果如下：\n{}".format(lott.winner_info())
                                else:
                                    msg = "HTTP Eror: {}\n{}".format(r.status_code, r.text)
                    elif sec_command=="verify":
                        if time.time() > lott.end_time:
                            msg = "请发送以下内容至 https://api.random.org/json-rpc/2/invoke 来确认结果由random.org返回\n"
                            reply_action = reply_message_action(receive, msg)
                            action_list.append(reply_action)
                            res_json = json.loads(lott.random_res)
                            req_json = {
                                "jsonrpc": "2.0",
                                "method": "verifySignature",
                                "params": {
                                    "random":res_json["result"]["random"],
                                    "signature":res_json["result"]["signature"]
                                },
                                "id": lott.id
                            }
                            msg = json.dumps(req_json)
                            # print("verifying msg:\n{}".format(msg))
                            reply_action = reply_message_action(receive, msg)
                            action_list.append(reply_action)
                            msg = ""
                        else:
                            msg = "抽奖未结束，无法验证抽奖"
        if isinstance(msg, str):
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