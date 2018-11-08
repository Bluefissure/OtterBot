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


def crawl_dps(boss, job, day=0):
    try:
        print("boss:{} job:{} day:{}".format(boss,job,day))
        fflogs_url = 'https://www.fflogs.com/zone/statistics/table/%s/dps/%s/100/8/1/75/1000/7/0/Global/%s/All/0/normalized/single/0/-1/'%(boss.quest.quest_id,boss.boss_id,job.name)
        r = requests.get(url=fflogs_url)
        tot_days = 0
        percentage_list = [10,25,50,75,95,99]
        atk_res = {}
        for perc in percentage_list:
            re_str = 'series%s'%(perc)+r'.data.push\([+-]?(0|([1-9]\d*))(\.\d+)?\)'
            ptn = re.compile(re_str)
            find_res = ptn.findall(r.text)
            print("url:{}".format(fflogs_url))
            # print("find_res:{}".format(json.dumps(find_res)))
            # print("find_res[day]:{}".format(json.dumps(find_res[day])))
            # print("id(find_res):{}".format(id(find_res)))
            atk_res[str(perc)] = find_res[day]
            ss = atk_res[str(perc)][1]+atk_res[str(perc)][2]
            if(ss==""):
                ss = "0"
            atk = float(ss)
            atk_res[str(perc)] = atk
            # tot_days = len(find_res)
        return atk_res
    except IndexError as e:
        return "Error: {}".format(e)



def QQCommand_dps(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        receive_msg = receive["message"].replace('/dpscheck','',1).strip()
        receive_msg = receive_msg.replace('/dps','',1).strip()
        boss_list = Boss.objects.all()
        boss_obj = None
        msg = ""
        for boss in boss_list:
            try:
                boss_nicknames = json.loads(boss.nickname)["nickname"]
            except KeyError:
                boss_nicknames = []
            boss_nicknames.append(boss.name)
            boss_nicknames.append(boss.cn_name)
            boss_nicknames.sort(key=lambda x:len(x),reverse=True)
            for item in boss_nicknames:
                if(receive_msg.find(item)==0):
                    receive_msg = receive_msg.replace(item,'',1).strip()
                    boss_obj = boss
                    break
            if(boss_obj):
                break
        if(not boss_obj):
            msg = "未能定位Boss:%s"%(receive_msg)
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
                job_nicknames.sort(key=lambda x:len(x),reverse=True)
                for item in job_nicknames:
                    if(receive_msg.find(item)==0):
                        receive_msg = receive_msg.replace(item,'',1).strip()
                        job_obj = job
                        break
                if(job_obj):
                    break
            if(not job_obj):
                msg = "未能定位职业:%s"%(receive_msg)
            else:
                day = math.ceil((int(time.time())-boss.cn_add_time)/(24*3600))
                if("国际服" in receive_msg):
                    day = -1
                    receive_msg = receive_msg.replace("国际服","")
                atk_res = crawl_dps(boss=boss_obj,job=job_obj,day=day)
                if type(atk_res)==str:
                    msg = "\nBoss:{}职业:{}第{}日的数据未抓取，请联系管理员抓取\n".format(boss,job,day)
                    msg += atk_res
                else:
                    if(receive_msg=="all" or receive_msg.strip()==""):
                        atk_dict = atk_res
                        print(json.dumps(atk_dict))
                        percentage_list = [10,25,50,75,95,99]
                        msg = "%s %s day#%s:\n"%(boss.cn_name,job.cn_name,day)
                        for perc in percentage_list:
                            msg += "%s%% : %.2f\n"%(perc,atk_dict[str(perc)])
                        msg = msg.strip()
                    else:
                        try:
                            atk = float(receive_msg)
                            assert(atk >= 0)
                        except:
                            msg = "DPS数值解析失败:%s"%(receive_msg)
                        else:
                            atk_dict = atk_res
                            percentage_list = [0,10,25,50,75,95,99]
                            atk_dict.update({"0":0})
                            logging.debug("atk_dict:"+json.dumps(atk_dict))
                            atk_list = [atk_dict[str(i)] for i in percentage_list]
                            idx = 0
                            while(idx<len(percentage_list) and atk>atk_dict[str(percentage_list[idx])]):
                                idx += 1
                            if(idx >= len(percentage_list)):
                                #msg = "%s %s %.2f day#%s 99%%+"%(boss.cn_name,job.cn_name,atk,day)
                                msg = "%s %s %.2f 99%%+"%(boss.cn_name,job.cn_name,atk)
                            else:
                                calc_perc = ((atk-atk_list[idx-1])/(atk_list[idx]-atk_list[idx-1]))*(percentage_list[idx]-percentage_list[idx-1])+percentage_list[idx-1]
                                if(calc_perc < 10):
                                    msg = "%s %s %.2f 10%%-"%(boss.cn_name,job.cn_name,atk)
                                else:
                                    #msg = "%s %s %.2f day#%s %.2f%%"%(boss.cn_name,job.cn_name,atk,day,calc_perc)
                                    msg = "%s %s %.2f %.2f%%"%(boss.cn_name,job.cn_name,atk,calc_perc)
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