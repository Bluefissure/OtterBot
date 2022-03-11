from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import math
import traceback
import re

def Critical(Crit):
    Rate = ((int(200*(Crit-400)/1900)+50)/1000)*100
    Strength = (int(200*(Crit-400)/1900)+1400)/1000
    NextCrit,NextRate = Crit,Rate
    while NextRate == Rate:
        NextCrit +=1
        NextRate = (int(200*(NextCrit-400)/1900)+50)/1000
    return Rate, Strength, NextCrit
def Direct(DH):
    Rate = (int(550*(DH-400)/1900)/1000)*100
    NextDH,NextRate = DH,Rate
    while NextRate == Rate:
        NextDH +=1
        NextRate = int(550*(NextDH-400)/1900)/1000
    return Rate,NextDH
def Determination(Det):
    Damage = (1000+int(140*(Det-390)/1900))/1000
    NextDet,NextDamage = Det,Damage
    while NextDamage == Damage:
        NextDet +=1
        NextDamage = (1000+int(140*(NextDet-390)/1900))/1000
    return NextDamage,NextDet
def Tenacity(Ten):
    OutDamage = (1000+int(100*(Ten-400)/1900))/1000
    InDamage = ((1000-int(100*(Ten-400)/1900))/1000)*100
    NextTen,NextOutDamage = Ten,OutDamage
    while NextOutDamage == OutDamage:
        NextTen +=1
        NextOutDamage = (1000+int(100*(NextTen-400)/1900))/1000
    return OutDamage,InDamage,NextTen
def Speed(Spe):
    GCDList = ['1.5', '2.0', '2.5', '2.8', '3.0', '4.0']
    result = []
    for GCD in GCDList:
        result.append((int(float(GCD)*1000*(1000+math.ceil(130*(400-Spe)/1900))/10000)/100))
    GCDResult = dict(zip(GCDList,result))
    GCDResult['DOT'] = (1000+int(130*(Spe-400)/1900))/1000
    Next25,Next28,Next25speed,Next28speed = GCDResult['2.5'],GCDResult['2.8'],Spe,Spe
    while Next25 == GCDResult['2.5']:
        Next25speed +=1
        Next25 = (int(2.5*1000*(1000+math.ceil(130*(400-Next25speed)/1900))/10000)/100)
    while Next28 == GCDResult['2.8']:
        Next28speed +=1
        Next28 = (int(2.8*1000*(1000+math.ceil(130*(400-Next28speed)/1900))/10000)/100)
    GCDResult['Next25speed'] = Next25speed
    GCDResult['Next28speed'] = Next28speed
    return GCDResult 
def QQCommand_fsx(*args,**kwargs):
    try:
        Receive = kwargs["receive"]
        action_list = []
        s_msg = Receive["message"].replace("/fsx","",1).strip()
        Msg = '版本 6.0 Lv90\n'
        MatchList = re.findall(r'\d+',s_msg)
        Number = -1
        if (MatchList):
            Number = int(MatchList[0])
            Number = min(Number, 99999)
            Number = max(Number, 390)
        if s_msg.find("help")==0 or s_msg=="" or Number < 390:
            Msg = '计算副属性,参数有暴击、直击、信念、坚韧、速度\n如：/fsx 暴击 2400\n参考地址https://www.akhmorning.com/allagan-studies/stats/'
        elif '暴击' in s_msg:
            Msg += '暴击 {0} 的计算结果：\n暴击率：{1[0]}%\n暴击伤害：{1[1]}\n下个临界点:暴击 {1[2]}'.format(Number,Critical(Number))
        elif '直击' in s_msg:
            Msg += '直击 {0} 的计算结果：\n直击率：{1[0]}%\n直击伤害固定为125%。\n下个临界点:直击 {1[1]}'.format(Number,Direct(Number))
        elif '信念' in s_msg:
            Msg += '信念 {0} 的计算结果：\n伤害增益：{1[0]}倍\n下个临界点:信念 {1[1]}'.format(Number,Determination(Number))
        elif '坚韧' in s_msg:
            Msg += '坚韧 {0} 的计算结果：\n伤害增益：{1[0]}倍（仅防护职业）\n受击伤害：{1[1]}%\n下个临界点:坚韧 {1[2]}'.format(Number,Tenacity(Number))
        elif '速' in s_msg:
            Msg += '速度 {0} 的计算结果：\nDOT收益:{1[DOT]}\n复唱:{1[2.5]}s\n1.5s:{1[1.5]}s\n2.0s:{1[2.0]}s\n2.8s:{1[2.8]}s\n3.0s:{1[3.0]}s\n4.0s:{1[4.0]}s\n下个临界点:\n2.5s: {1[Next25speed]}\n2.8s: {1[Next28speed]}'.format(Number,Speed(Number))
        else:
            Msg = ' 错误参数：{}'.format(s_msg)
        reply_action = reply_message_action(Receive, Msg)
        action_list.append(reply_action)
    except Exception as e:
        Msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(Receive, Msg))
    return action_list
