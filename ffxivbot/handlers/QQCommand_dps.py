from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import math
import re
import traceback


def QQCommand_dps(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        receive_msg = receive["message"].replace("/dpscheck", "", 1).strip()
        receive_msg = receive_msg.replace("/dps", "", 1).strip()
        boss_list = Boss.objects.all()
        boss_obj = None
        msg = ""
        CN_source = False
        msg = "dps command is halt due to "

        if receive_msg.find("help") == 0 or receive_msg == "":
            msg = """1.  查询总排名
/dps [Boss] [职业]
2.  查询指定天数总排名
/dps [Boss] [职业] day#[天数]
3.  查询dps排名
/dps [Boss] [职业] [数值]
4.  查询指定天数dps排名
/dps [Boss] [职业] day#[天数] [数值]
5.  查询国服dps排名
/dps ... 国服
6.  查询rdps
/dps ... rdps"""
        else:
            for boss in boss_list:
                try:
                    boss_nicknames = json.loads(boss.nickname)["nickname"]
                except KeyError:
                    boss_nicknames = []
                boss_nicknames.append(boss.name)
                boss_nicknames.append(boss.cn_name)
                boss_nicknames.sort(key=len, reverse=True)
                for item in boss_nicknames:
                    if receive_msg.find(item) == 0:
                        receive_msg = receive_msg.replace(item, "", 1).strip()
                        boss_obj = boss
                        break
                if boss_obj:
                    break
            if not boss_obj:
                msg = "未能定位Boss:%s" % (receive_msg)
            else:
                job_list = Job.objects.all()
                job_obj = None
                for job in job_list:
                    try:
                        job_nicknames = json.loads(job.nickname)["nickname"]
                    except KeyError:
                        job_nicknames = []
                    job_nicknames.append(job.name)
                    job_nicknames.append(job.cn_name)
                    job_nicknames.sort(key=len, reverse=True)
                    for item in job_nicknames:
                        if receive_msg.find(item) == 0:
                            receive_msg = receive_msg.replace(item, "", 1).strip()
                            job_obj = job
                            break
                    if job_obj:
                        break
                if not job_obj:
                    msg = "未能定位职业:%s" % (receive_msg)
                else:
                    boss = boss_obj
                    job = job_obj
                    day = math.floor(
                        (int(time.time()) - boss_obj.cn_add_time) / (24 * 3600)
                    )
                    if "CN" in receive_msg or "国服" in receive_msg:
                        CN_source = True
                        receive_msg = receive_msg.replace("CN", "", 1).replace(
                            "国服", "", 1
                        )
                    dps_type = "adps"
                    if "rdps" in receive_msg:
                        dps_type = "rdps"
                        receive_msg = receive_msg.replace("rdps", "", 1)
                    if "国际服" in receive_msg:
                        receive_msg = receive_msg.replace("国际服", "day#-1")
                    if boss.frozen:
                        day = -1
                    if "day#" in receive_msg:
                        tmp_day = int(receive_msg.split(" ")[0].replace("day#", ""))
                        day = tmp_day
                        receive_msg = receive_msg.replace(
                            "day#{}".format(tmp_day), "", 1
                        )
                    atk_res = crawl_dps(
                        boss=boss_obj,
                        job=job_obj,
                        day=day,
                        CN_source=CN_source,
                        dps_type=dps_type,
                    )
                    info_msg = "国服" if CN_source else "国际服"
                    info_msg += "({})".format(dps_type)
                    if isinstance(atk_res, str):
                        msg = "\nBoss:{}职业:{}第{}日的{}数据未抓取，请联系管理员排查\n".format(
                            boss, job, day, info_msg
                        )
                        msg += atk_res
                    else:
                        day = atk_res.get("day", day)
                        if receive_msg == "all" or receive_msg.strip() == "":
                            atk_dict = atk_res
                            print(json.dumps(atk_dict))
                            percentage_list = [10, 25, 50, 75, 95, 99, 100]
                            msg = "{} {} {} day#{}:\n".format(
                                boss.cn_name, job.cn_name, info_msg, day,
                            )
                            for perc in percentage_list:
                                msg += "%s%%: %.2f\n" % (perc, atk_dict[str(perc)])
                            msg = msg.strip()
                        else:
                            try:
                                atk = float(receive_msg)
                                assert atk >= 0
                            except ValueError:
                                msg = "DPS数值解析失败:%s" % (receive_msg)
                            else:
                                atk_dict = atk_res
                                percentage_list = [0, 10, 25, 50, 75, 95, 99, 100]
                                atk_dict.update({"0": 0})
                                logging.debug("atk_dict:" + json.dumps(atk_dict))
                                atk_list = [atk_dict[str(i)] for i in percentage_list]
                                idx = 0
                                while (
                                    idx < len(percentage_list)
                                    and atk > atk_dict[str(percentage_list[idx])]
                                ):
                                    idx += 1
                                if idx >= len(percentage_list):
                                    # msg = "%s %s %.2f day#%s 99%%+"%(boss.cn_name,job.cn_name,atk,day)
                                    msg = "%s %s %.2f 99%%+" % (
                                        boss.cn_name,
                                        job.cn_name,
                                        atk,
                                    )
                                else:
                                    # fmt: off
                                    calc_perc = ((atk-atk_list[idx-1])/(atk_list[idx]-atk_list[idx-1]))*(percentage_list[idx]-percentage_list[idx-1])+percentage_list[idx-1]  # math here
                                    # fmt: on
                                    if calc_perc < 10:
                                        msg = "%s %s %.2f 10%%-" % (
                                            boss.cn_name,
                                            job.cn_name,
                                            atk,
                                        )
                                    else:
                                        # msg = "%s %s %.2f day#%s %.2f%%"%(boss.cn_name,job.cn_name,atk,day,calc_perc)
                                        msg = "%s %s %.2f %.2f%%" % (
                                            boss.cn_name,
                                            job.cn_name,
                                            atk,
                                            calc_perc,
                                        )
                                msg += "\n计算基于{} day#{}数据".format(info_msg, day)
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
