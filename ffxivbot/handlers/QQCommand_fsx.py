from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import math
import traceback
import re

def QQCommand_fsx(*args,**kwargs):
    try:
        bot = kwargs["bot"]
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        action_list = []
        s_msg = receive["message"].replace("/fsx","",1).strip()
        nlv = 3300
        msg = '版本 5.0 Lv80 等级基数:3300\n'
        match_list = re.findall(r'\d+',s_msg)
        number = -1
        if (match_list):
            number = int(match_list[0])
            number = min(number, 99999)
            number = max(number, 0)
        if s_msg.find("help")==0 or s_msg=="" or number < 0:
            msg = '计算副属性,参数有暴击、直击、信念、坚韧、速度\n如：/fsx 暴击 2400'
        elif '暴击' in s_msg:
            critical = number - 380
            per = (math.floor(200 * critical/nlv) + 50)/10
            bonus = (1000 + math.floor(200 * critical/nlv) + 400)/10
            edmg = 1 + (per/100 * (bonus-100)/100)
            per_tmp,cri_tmp = per,critical+380
            while per_tmp == per:
                cri_tmp += 1
                per_tmp = (math.floor(200 * (cri_tmp-380)/nlv) + 50)/10
            msg += '暴击 {} 的计算结果(基数:380)：\n暴击率：   {}%\n暴击伤害：   {}%\n预期收益：   {}\n下个临界点:暴击 {}'.format(critical+380,per,bonus,edmg,cri_tmp)
          
        elif '直击' in s_msg:
            direct = number - 380
            per = (math.floor(550 * direct/nlv))/10
            per_tmp,dir_tmp = per,direct+380
            while per_tmp == per:
                dir_tmp += 1
                per_tmp = (math.floor(550 * (dir_tmp-380)/nlv))/10
            msg += '直击 {} 的计算结果(基数:380)：\n直击率：    {}%\n直击伤害固定为125%。\n下个临界点:直击 {}'.format(direct+380,per,dir_tmp)
         
        elif '信念' in s_msg:
            determination = number - 340
            mult = (1000 + math.floor(130 * determination/nlv))/1000
            mult_tmp,det_tmp = mult,determination+340
            while mult_tmp == mult:
                det_tmp += 1
                mult_tmp = (1000 + math.floor(130 * (det_tmp-340)/nlv))/1000
            msg += '信念 {} 的计算结果(基数:340)：\n伤害增益：{}倍\n下个临界点:信念 {}'.format(determination+340,mult,det_tmp)
    
        elif '坚韧' in s_msg:
            tenacity = number  - 380
            mult = (1000 + math.floor(100 * tenacity/nlv))/1000
            mit = (1000 - math.floor(100 * tenacity/nlv))/10
            mult_tmp,ten_tmp = mult,tenacity+380
            while mult_tmp == mult:
                ten_tmp += 1
                mult_tmp = (1000 + math.floor(100 * (ten_tmp-380)/nlv))/1000
            msg += '坚韧 {} 的计算结果(基数:380)：\n伤害增益：{}倍（仅防护职业）\n受击伤害：{}%\n下个临界点:坚韧 {}'.format(tenacity+380,mult,mit,ten_tmp)
  
        elif '速' in s_msg:
            speed = number - 380
            mult = (1000 + math.floor(130 * speed/nlv))/1000  
            cd_15 = math.floor(math.floor(100 * 100 * (math.floor(1500 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_20 = math.floor(math.floor(100 * 100 * (math.floor(2000 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_25 = math.floor(math.floor(100 * 100 * (math.floor(2500 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_28 = math.floor(math.floor(100 * 100 * (math.floor(2800 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_30 =  math.floor(math.floor(100 * 100 * (math.floor(3000 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_80 = math.floor(math.floor(100 * 100 * (math.floor(8000 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_25_tmp,cd_28_tmp,speed_tmp1,speed_tmp2 = cd_25,cd_28,speed+380,speed+380
            while cd_25_tmp == cd_25:
                speed_tmp1 += 1
                cd_25_tmp = math.floor(math.floor(100 * 100 * (math.floor(2500 * (1000 - math.floor(130 * (speed_tmp1-380)/nlv))/1000)/1000))/100)/100
            while cd_28_tmp == cd_28:
                speed_tmp2 += 1
                cd_28_tmp = math.floor(math.floor(100 * 100 * (math.floor(2800 * (1000 - math.floor(130 * (speed_tmp2-380)/nlv))/1000)/1000))/100)/100
            msg += '速度 {} 的计算结果(基数:380)：\nDoT收益:    {}\n复唱:    {}s\n1.5s:    {}s\n2.0s:    {}s\n2.8s:    {}s\n3.0s:    {}s\n复活(8s):    {}s\n下个临界点:\n2.5s: {}\n2.8s: {}'.format(speed+380,mult,cd_25,cd_15,cd_20,cd_28,cd_30,cd_80,speed_tmp1,speed_tmp2)
        else:
            msg = ' 错误参数：{}'.format(s_msg)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
    return action_list
