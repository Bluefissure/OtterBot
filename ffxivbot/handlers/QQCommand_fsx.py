from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *

def QQCommand_fsx(*args, **kwargs):
    try:
        bot = kwargs["bot"]
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        action_list = []
        s_msg = receive["message"].replace("/fsx","",1).strip()
        nlv=3300
        msg = '版本 5.0 Lv80 等级基数:3300\n'
        if '暴击' in s_msg:
            critical = int(s_msg.replace("暴击","")) - 380
            per = (math.floor(200 * critical/nlv) + 50)/10
            bonus = (1000 + math.floor(200 * critical/nlv) + 400)/10
            edmg = 1 + (per/100 * (bonus-100)/100)
            msg += '暴击 {} 的计算结果(基数:380)：\n暴击率：   {}%\n暴击伤害：   {}%\n预期收益：   {}'.format(critical+380,per,bonus,edmg)
        
        elif '直击' in s_msg:
            direct = int(s_msg.replace("直击","")) - 380
            per = (math.floor(550 * direct/nlv))/10
            msg += '直击 {} 的计算结果(基数:380)：\n直击率：    {}%\n直击伤害固定为125%。'.format(direct+380,per)
        
        elif '信念' in s_msg:
            determination = int(s_msg.replace("信念","")) - 340
            mult = (1000 + math.floor(130 * determination/nlv))/1000
            msg += '信念 {} 的计算结果(基数:340)：\n伤害增益：{}倍'.format(determination+340,mult)

        elif '坚韧' in s_msg:
            tenacity = int(s_msg.replace("坚韧","")) - 380
            mult = (1000 + math.floor(100 * tenacity/nlv))/1000
            mit = (1000 - math.floor(100 * tenacity/nlv))/10
            msg += '坚韧 {} 的计算结果(基数:380)：\n伤害增益：{}倍（仅防护职业）\n受击伤害：{}%'.format(tenacity+380,mult,mit)

        elif '速度' in s_msg:
            speed = int(s_msg.replace("速度","")) - 380
            mult = (1000 + math.floor(130 * speed/nlv))/1000  
            cd_15 = math.floor(math.floor(100 * 100 * (math.floor(1500 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_20 = math.floor(math.floor(100 * 100 * (math.floor(2000 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_25 = math.floor(math.floor(100 * 100 * (math.floor(2500 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_30 =  math.floor(math.floor(100 * 100 * (math.floor(3000 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            cd_80 = math.floor(math.floor(100 * 100 * (math.floor(8000 * (1000 - math.floor(130 * speed/nlv))/1000)/1000))/100)/100
            msg += '速度 {} 的计算结果(基数:380)：\nDoT收益:    {}\n复唱:    {}s\n1.5s:    {}s\n2.0s:    {}s\n3.0s:    {}s\n复活(8s):    {}s'.format(speed+380,mult,cd_25,cd_15,cd_20,cd_30,cd_80)
        else:
            msg = '参数 {} 错误'.format(s_msg)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
    return action_list
