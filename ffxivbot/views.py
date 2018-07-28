# -*- coding: utf-8 -*-
from django.shortcuts import render, Http404, HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.template import Context, RequestContext, loader
from django.http import HttpResponse
from django.http import JsonResponse
from django.db.models import Q
from django.core.files.base import ContentFile
from django.utils import timezone
from collections import OrderedDict
from django.views.decorators.csrf import csrf_exempt
import datetime
import pytz
import re
import json
import pymysql
import time
from ffxivbot.models import *
from hashlib import md5
import math
import requests
import base64
import random,sys
import traceback  
import codecs
import html
import hmac
from bs4 import BeautifulSoup
import urllib
# Create your views here.

#Base Constant
QQPOST_URL = 'http://***.***.***.***:****'
ACCESS_TOKEN = "************"
SECRET_KEY = "*********"

#random.org
RANDOMORG_TOKEN = "******************************************"

#whatanime.ga
WHATANIME_TOKEN = "******************************************"
WHATANIME_API_URL = "https://whatanime.ga/api/search?token="+WHATANIME_TOKEN

#ff14.huijiwiki.com
FF14WIKI_BASE_URL = "https://ff14.huijiwiki.com"
FF14WIKI_API_URL = "https://cdn.huijiwiki.com/ff14/api.php"

#sorry API
SORRY_BASE_URL = "https://sorry.xuty.tk"


#Tuling API
TULING_API_URL = "http://openapi.tuling123.com/openapi/api/v2"
TULING_API_KEY = "************************************"

#Baidu Cloud API
BAIDU_IMAGE_API_KEY = "*********************************"
BAIDU_IMAGE_SECRET_KEY = "*********************************"
BAIDU_IMAGE_ACCESS_TOKEN_URL = 'https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id=%s&client_secret=%s'%(BAIDU_IMAGE_API_KEY,BAIDU_IMAGE_SECRET_KEY)
BAIDU_IMAGE_ACCESS_TOKEN = "******************************************************************"
BAIDU_IMAGE_CENSOR_URL = 'https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/user_defined?access_token='+BAIDU_IMAGE_ACCESS_TOKEN





QQBOT_LIST = ["2854196306"]

TIMEFORMAT = "%Y-%m-%d %H:%M:%S"
TIMEFORMAT_MDHMS = "%m-%d %H:%M:%S"

def refresh_baidu_access_token():
    r = requests.post(url=BAIDU_RECORD_ACCESS_TOKEN_URL)
    r = json.loads(r.text)
    print(r)





def get_item_info(url):
    r = requests.get(url,timeout=3)
    bs = BeautifulSoup(r.text,"html.parser")
    item_info = bs.find_all(class_='infobox-item ff14-content-box')[0]
    item_title = item_info.find_all(class_='infobox-item--name-title')[0]
    item_title_text = item_title.get_text().strip()
    if item_title.img and item_title.img.attrs["alt"]=="Hq.png":
        item_title_text += "(HQ)"
    print("item_title_text:%s"%(item_title_text))
    item_img = item_info.find_all(class_='item-icon--img')[0]
    item_img_url = item_img.img.attrs['src'] if item_img and item_img.img else ""
    item_content = item_info.find_all(class_='ff14-content-box-block')[0]
    #print(item_info.prettify())
    item_content_text = item_title_text
    try:
        item_content_text = item_content.p.get_text().strip()
    except Exception as e:
        traceback.print_exc() 
    res_data = {
        "url":url,
        "title":item_title_text,
        "content":item_content_text,
        "image":item_img_url,
    }
    return res_data

def search_item(name):
    search_url = FF14WIKI_API_URL+"?format=json&action=parse&title=ItemSearch&text={{ItemSearch|name=%s}}"%(name)
    r = requests.get(search_url,timeout=3)
    res_data = json.loads(r.text)
    bs = BeautifulSoup(res_data["parse"]["text"]["*"],"html.parser")
    if("没有" in bs.p.string):
        return False
    res_num = int(bs.p.string.split(" ")[1])
    item_names = bs.find_all(class_="item-name")
    if len(item_names) == 1:
        item_name = item_names[0].a.string
        item_url = FF14WIKI_BASE_URL + item_names[0].a.attrs['href']
        print("%s %s"%(item_name,item_url))
        res_data = get_item_info(item_url)
    else:
        item_img = bs.find_all(class_="item-icon--img")[0]
        item_img_url = item_img.img.attrs['src']
        search_url = FF14WIKI_BASE_URL+"/wiki/ItemSearch?name="+urllib.parse.quote(name)
        res_data = {
            "url":search_url,
            "title":"%s 的搜索结果"%(name),
            "content":"在最终幻想XIV中找到了 %s 个物品"%(res_num),
            "image":item_img_url,
        }
    print("res_data:%s"%(res_data))
    return res_data



def check_contain_chinese(check_str):
    for ch in check_str:
        if u'\u4e00' <= ch <= u'\u9fff':
            return True
    return False
def whatanime(receive):
    try:
        tmp = receive["message"]
        tmp = tmp[tmp.find("url="):-1]
        tmp = tmp.replace("url=","")
        img_url = tmp.replace("]","")
        print("getting img_url:%s"%(img_url))
        r = requests.get(img_url,timeout=30)
        print("img got")
        imgb64 = base64.b64encode(r.content)
        print("whatanime post")
        r2 = requests.post(url=WHATANIME_API_URL,data={"image":imgb64.decode()},timeout=30)
        print("WhatAnime_res:\n%s"%(r2.text))
        if(r2.status_code==200):
            print("finished whatanime\nParsing.........")
            json_res = json.loads(r2.text)
            if(len(json_res["docs"])==0):
                msg = "未找到所搜索的番剧"
            else:
                anime = json_res["docs"][0]
                title_list = ["title_chinese","title","title_native","anime"]
                title=""
                for item in anime["synonyms_chinese"]:
                    if(item!="" and check_contain_chinese(item) and title==""):
                        title = item
                        break
                for item in title_list:
                    if(anime[item]!="" and  check_contain_chinese(anime[item])and title==""):
                        title = anime[item]
                        break
                for item in title_list:
                    if(anime[item]!="" and title==""):
                        title = anime[item]
                        break

                duration = [(int(anime["from"])//60,int(anime["from"])%60),(int(anime["to"])//60,int(anime["to"])%60)]
                msg = "%s\nEP#%s\n%s:%s-%s:%s\n相似度:%.2f%%"%(title,anime["episode"],duration[0][0],duration[0][1],duration[1][0],duration[1][1],float(anime["similarity"])*100)
                msg = msg+"\nPowered by whatanime.ga"
        elif (r2.status_code==413):
            msg = "图片太大啦，请压缩至1M"
        else:
            msg = "Error at whatanime API, status code %s"%(r2.status_code)
    except Exception as e:
        traceback.print_exc() 
        msg = "Error:%s \nTell developer to check the log."%(e)
    print("WhatAnime_msg:\n%s"%(msg))
    if(receive["message_type"]=="private"):
        jdata = {"user_id":receive["user_id"],"message":msg}
        s=requests.post(url=QQPOST_URL+'/send_private_msg_async?access_token='+ACCESS_TOKEN,data=jdata,timeout=10)
    elif(receive["message_type"]=="group"):
        jdata = {"group_id":receive["group_id"],"message":"[CQ:at,qq=%s]\n"%(receive["user_id"])+msg}
        s=requests.post(url=QQPOST_URL+'/send_group_msg_async?access_token=2ASdOeYCOyp',data=jdata,timeout=10)


def get_group_member_info(group_id,user_id):
    jdata = {"group_id":group_id,"user_id":user_id}
    s = requests.post(url=QQPOST_URL+'/get_group_member_info?access_token='+ACCESS_TOKEN,data=jdata,timeout=10)
    res_json = json.loads(s.text)
    return res_json["data"]

def send_group_msg(group_id,msg,at_user_id=None):
    if at_user_id:
        msg = "[CQ:at,qq=%s] "%(at_user_id)+msg
    jdata = {"group_id":group_id,"message":msg}
    print("jdata:%s"%(json.dumps(jdata)))
    s=requests.post(url=QQPOST_URL+'/send_group_msg_async?access_token=2ASdOeYCOyp',data=jdata,timeout=10)
    res_json = json.loads(s.text)
    return res_json

def send_private_msg(user_id,msg):
    jdata = {"user_id":user_id,"message":msg}
    print("jdata:%s"%(json.dumps(jdata)))
    s=requests.post(url=QQPOST_URL+'/send_private_msg_async?access_token=2ASdOeYCOyp',data=jdata,timeout=10)
    res_json = json.loads(s.text)
    return res_json


def group_ban(group_id,user_id,duration=60):
    jdata = {"group_id":group_id,"user_id":user_id,"duration":duration}
    s=requests.post(url=QQPOST_URL+'/set_group_ban?access_token=2ASdOeYCOyp',data=jdata,timeout=10)
    res_json = json.loads(s.text)
    return res_json

def send_like(user_id,times=1):
    jdata = {"user_id":user_id,"times":times}
    print("like_data:%s"%(json.dumps(jdata)))
    s=requests.post(url=QQPOST_URL+'/send_like?access_token=2ASdOeYCOyp',data=jdata,timeout=10)
    res_json = json.loads(s.text)
    print("like_res:%s"%(json.dumps(res_json)))
    return res_json

def delete_msg(message_id):
    jdata = {"message_id":message_id}
    s=requests.post(url=QQPOST_URL+'/delete_msg?access_token=2ASdOeYCOyp',data=jdata,timeout=10)
    res_json = json.loads(s.text)
    return res_json


def image_censor_url(image_url):
    data = {
        "imgUrl":image_url
    }
    r = requests.post(url=BAIDU_IMAGE_CENSOR_URL,data=data)
    print(r.text)
    return json.loads(r.text)

def image_censor(receive):
    tmp = receive["message"]
    tmp = tmp[tmp.find("url="):-1]
    tmp = tmp.replace("url=","")
    img_url = tmp.replace("]","")
    censor_res = image_censor_url(img_url)
    if("error_msg" in censor_res.keys()):
        return
    if(censor_res["conclusion"]=="不合规" or censor_res["conclusion"]=="疑似"):
        cnt = 0
        msg = "[CQ:at,qq=%s]"%(receive["user_id"])+" 所发图片由于：\n"
        for item in censor_res["data"]:
            if("公众" in item["msg"] or "政治敏感" in item["msg"]):
                msg += "%s：\n"%(item["msg"])
                for star in item["stars"]:
                    msg += "    %.2f%%%s\n"%(float(star["probability"])*100,star["name"])
            else:
                msg += "%.2f%%%s\n"%(float(item["probability"])*100,item["msg"])
            if(("色情" in item["msg"] or "政治敏感" in item["msg"])):
                cnt += 1
        msg += "而触发图片审核机制，请管理员处理。"
        if(cnt > 0):
            send_group_msg(receive["group_id"],msg)


def calculateForecastTarget(unixSeconds): 
    # Thanks to Rogueadyn's SaintCoinach library for this calculation.
    # lDate is the current local time.
    # Get Eorzea hour for weather start
    bell = unixSeconds / 175

    # Do the magic 'cause for calculations 16:00 is 0, 00:00 is 8 and 08:00 is 16
    increment = int(bell + 8 - (bell % 8)) % 24

    # Take Eorzea days since unix epoch
    totalDays = unixSeconds // 4200
    # totalDays = (totalDays << 32) >>> 0; # Convert to uint

    calcBase = totalDays * 100 + increment

    step1 = (((calcBase << 11)%(0x100000000)) ^ calcBase)
    step2 = (((step1 >> 8)%(0x100000000)) ^ step1)
    
    return step2 % 100

def getEorzeaHour(unixSeconds):
    bell = (unixSeconds / 175) % 24;
    return int(bell)

def getWeatherTimeFloor(unixSeconds):
    # Get Eorzea hour for weather start
    bell = (unixSeconds / 175) % 24
    startBell = bell - (bell % 8)
    startUnixSeconds = round(unixSeconds - (175 * (bell - startBell)))
    return startUnixSeconds

def checkGale(unixSeconds):
    chance = calculateForecastTarget(unixSeconds)
    # print("chance for %s: %s"%(unixSeconds,chance))
    return (30 <= chance < 60)

def eurekaGale(count):
    unixSeconds = int(time.time())
    weatherStartTime = getWeatherTimeFloor(unixSeconds);
    count = min(count,10)
    count = max(count,-10)
    match = 0
    msg = ""
    now_time = weatherStartTime
    tryTime = 0
    if count >= 0:
        while(match < count and tryTime <= 1000):
            tryTime += 1
            if(checkGale(now_time)):
                print("%s %s"%(getEorzeaHour(now_time),now_time))
                msg += "ET: %s:00\tLT: %s\n"%(getEorzeaHour(now_time),time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)))
                # print("find gale:"+time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)))
                match += 1
            # print("now_time: %s %s %s"%(getEorzeaHour(now_time),time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)),now_time))
            now_time += 8 * 175
    if count < 0:
        count = -count
        msg = ""
        while(match < count and tryTime <= 1000):
            tryTime += 1
            if(checkGale(now_time)):
                print("%s %s"%(getEorzeaHour(now_time),now_time))
                msg += "ET: %s:00\tLT: %s\n"%(getEorzeaHour(now_time),time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)))
                # print("find gale:"+time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)))
                match += 1
            # print("now_time: %s %s %s"%(getEorzeaHour(now_time),time.strftime(TIMEFORMAT_MDHMS,time.localtime(now_time)),now_time))
            now_time -= 8 * 175
    # print(msg)
    return msg.strip()



@csrf_exempt
def qqpost(req):
    try:
        receive = json.loads(req.body.decode())
        sig = hmac.new(b'pinkpink', req.body, 'sha1').hexdigest()
        received_sig = req.META.get("HTTP_X_SIGNATURE","unknow")[len('sha1='):]
        if(sig == received_sig):
            if (receive["post_type"] == "message"):
                if (receive["message"].find('/help')==0):
                    msg = "/cat : 云吸猫\n/gakki : 云吸gakki\n/bird : 云吸飞鸟\n/like : 赞\n/random(gate) : 掷骰子\n/search $item : 在最终幻想XIV中查询物品$item\n/dps $boss $job $dps : 在最终幻想XIV中查询DPS在对应BOSS与职业的logs排名（国际服同期数据）\n/pzz $cnt : 在最终幻想XIV中查询尤雷卡接下来$cnt次强风时间\n/anime $img : 查询$img对应番剧(只支持1M以内静态全屏截图)\n/gif : 生成沙雕GIF\n/about : 关于獭獭\n/donate : 援助作者"
                    msg = msg.strip()
                    reply_data = {"reply":msg}
                    if(receive["message_type"]=="group"):
                        reply_data["at_sender"] = "false"
                    return JsonResponse(reply_data)
                
                if (receive["message"] == '/cat'):
                    reply_data = {"reply":[{"type":"image","data":{"file":"cat/%s.jpg"%(random.randint(0,750))}}]}
                    if(receive["message_type"]=="group"):
                        reply_data["at_sender"] = "false"
                    return JsonResponse(reply_data)
                if (receive["message"] == '/gakki'):
                    reply_data = {"reply":[{"type":"image","data":{"file":"gakki/%s.jpg"%(random.randint(1,1270))}}]}
                    if(receive["message_type"]=="group"):
                        reply_data["at_sender"] = "false"
                    return JsonResponse(reply_data)
                if (receive["message"] == '/bird'):
                    jpg_cnt = 182
                    gif_cnt = 5
                    png_cnt = 65
                    idx = random.randint(1,jpg_cnt+gif_cnt+png_cnt)
                    img_path = "bird/%s.jpg"%(idx) if idx<=jpg_cnt else ("bird/%s.gif"%(idx-jpg_cnt) if idx-jpg_cnt<=gif_cnt else "bird/%s.png"%(idx-jpg_cnt-gif_cnt))
                    reply_data = {"reply":[{"type":"image","data":{"file":img_path}}]}
                    if(receive["message_type"]=="group"):
                        reply_data["at_sender"] = "false"
                    return JsonResponse(reply_data)
                if (receive["message"].find('/like')==0):
                    times = receive["message"].replace('/like','')
                    try:
                        times = int(times)
                    except:
                        times = 1
                    like_res = send_like(receive["user_id"],times=times)
                    if(like_res["status"]!="ok"):
                        reply_data = {"reply":"赞失败啦！！"}
                    else:
                        reply_data = {"reply":"赞了%s次！"%(times)}
                    return JsonResponse(reply_data)
                if (receive["message"].find('/search')==0):
                    name = receive["message"].replace('/search','')
                    name = name.strip()
                    res_data = search_item(name)
                    if res_data:
                        reply_data = {"reply":[{"type":"share","data":res_data}]}
                    else:
                        reply_data = {"reply":"在最终幻想XIV中没有找到 %s"%(name)}
                    return JsonResponse(reply_data)
                if (receive["message"].find('/about')==0):
                    res_data = {
                        "url":"https://github.com/Bluefissure/FFXIVBOT",
                        "title":"FFXIVBOT",
                        "content":"by Bluefissure",
                        "image":"https://i.loli.net/2018/05/06/5aeeda6f1fd4f.png",
                    }
                    reply_data = {"reply":[{"type":"share","data":res_data}]}
                    if(receive["message_type"]=="group"):
                        reply_data["at_sender"] = "false"
                    return JsonResponse(reply_data)
                if (receive["message"].find('/donate')==0):
                    #reply_data = {"reply":[{"type":"text","data":{"text":"我很可爱(*╹▽╹*)请给我钱（来租服务器养活獭獭）"}},{"type":"image","data":{"file":"alipay.jpg"}}],"at_sender":"false"}
                    reply_data = {"reply":[{"type":"text","data":{"text":"獭獭很可爱(*╹▽╹*)不用给钱啦獭獭已经买了好多零食"}}],"at_sender":"false"}
                    return JsonResponse(reply_data)
                if (receive["message"].find('/anime')==0):
                    print("anime_msg:%s"%(receive["message"]))
                    qq = int(receive["user_id"])
                    if(receive["message"] == '/anime'):
                        pass
                    elif ("CQ" in receive["message"] and "url=" in receive["message"]):
                        reply_data = whatanime(receive)
                if (receive["message"].find('/gate')==0):
                    try:
                        num = int(receive["message"].replace("/gate",""))
                    except:
                        num = 2
                    num = min(num, 3)
                    gate = random.randint(0,num-1)
                    choose_list = [i for i in range(num)]
                    random.shuffle(choose_list)
                    gate_idx = choose_list.index(gate)
                    gate_msg = "左边" if gate_idx==0 else "右边" if gate_idx==1 else "中间"
                    reply_data = {"reply":"掐指一算，[CQ:at,qq=%s]应该走%s门，信獭獭没错！"%(receive["user_id"],gate_msg),"at_sender":"false"}
                    print("reply_data:%s"%(reply_data))
                    return JsonResponse(reply_data)
                if (receive["message"].find('/random')==0):
                    score = random.randint(1,1000)
                    msg = str(score)
                    if(receive["message_type"]=="group"):
                        group_id = receive["group_id"]
                        grps = QQGroup.objects.filter(group_id=group_id)
                        if(len(grps)>0):
                            group = grps[0]
                            rss = RandomScore.objects.filter(user_id=receive["user_id"],group=group)
                            if(len(rss)>0):
                                rs = rss[0]
                            else:
                                rs = RandomScore(user_id=receive["user_id"],group=group)
                            rs.min_random = min(rs.min_random,score)
                            rs.max_random = max(rs.max_random,score)
                            rs.save()
                    reply_data = {"reply":"[CQ:at,qq=%s]掷出了"%(receive["user_id"])+msg+"点！","at_sender":"false"}
                    print("reply_data:%s"%(reply_data))
                    return JsonResponse(reply_data)


                if (receive["message"].find('/eureka')==0 or receive["message"].find('/pzz')==0):
                    receive_msg = receive["message"].replace("/eureka","").replace("/pzz","")
                    try:
                        cnt = int(receive_msg)
                    except:
                        cnt = 3

                    reply_data = {"reply":"接下来Eureka的强风天气如下：\n%s"%(eurekaGale(cnt)),"at_sender":"false"}
                    return JsonResponse(reply_data)
                if (receive["message"].find('/gif')==0):
                    sorry_dict = {"sorry":"好啊|就算你是一流工程师|就算你出报告再完美|我叫你改报告你就要改|毕竟我是客户|客户了不起啊|sorry 客户真的了不起|以后叫他天天改报告|天天改 天天改","wangjingze":"我就是饿死|死外边 从这跳下去|也不会吃你们一点东西|真香","jinkela":"金坷垃好处都有啥|谁说对了就给他|肥料掺了金坷垃|不流失 不蒸发 零浪费|肥料掺了金坷垃|能吸收两米下的氮磷钾","marmot":"啊~|啊~~~","dagong":"没有钱啊 肯定要做的啊|不做的话没有钱用|那你不会去打工啊|有手有脚的|打工是不可能打工的|这辈子不可能打工的","diandongche":"戴帽子的首先进里边去|开始拿剪刀出来 拿那个手机|手机上有电筒 用手机照射|寻找那个比较新的电动车|六月六号 两名男子再次出现|民警立即将两人抓获"}
                    sorry_name = {"sorry":"为所欲为","wangjingze":"王境泽","jinkela":"金坷垃","marmot":"土拨鼠","dagong":"窃格瓦拉","diandongche":"偷电动车"}
                    receive_msg = receive["message"].replace('/gif','',1).strip()
                    if receive_msg=="list":
                        msg = ""
                        for (k,v) in sorry_dict.items():
                            msg = msg + "%s : %s\n"%(k,sorry_name[k])
                    else:
                        now_template = ""
                        for (k,v) in sorry_dict.items():
                            if (receive_msg.find(k)==0):
                                now_template = k
                                break
                        if (now_template=="" or len(receive_msg)==0 or receive_msg=="help"):
                            msg = "/gif list : 目前可用模板\n/gif $template example : 查看模板$template的样例\n/gif $template $msg0|$msg1|... : 按照$msg0,$msg1...生成沙雕GIF\nPowered by sorry.xuty.tk"
                        else:
                            receive_msg = receive_msg.replace(now_template,"",1).strip()
                            if(receive_msg=="example"):
                                msg = sorry_dict[now_template]
                            else:
                                msgs = receive_msg.split('|')
                                cnt = 0
                                gen_data = {}
                                for sentence in msgs:
                                    sentence = sentence.strip()
                                    if(sentence==""):
                                        continue
                                    gen_data[str(cnt)] = sentence
                                    print("sentence#%s:%s"%(cnt,sentence))
                                    cnt += 1
                                if(cnt==0):
                                    msg = "至少包含一条字幕消息"
                                else:
                                    print("gen_data:%s"%(json.dumps(gen_data)))
                                    url = SORRY_BASE_URL + "/api/%s/make"%(now_template)
                                    try:
                                        s = requests.post(url=url,data=json.dumps(gen_data),timeout=2)
                                        img_url = SORRY_BASE_URL + s.text
                                        print("img_url:%s"%(img_url))
                                        msg = '[CQ:image,file='+img_url+']'
                                    except Exception as e:
                                        msg = "SORRY API ERROR:%s"%(e)
                                        print(msg)
                                        reply_data = {"reply":msg}  
                                        return JsonResponse(reply_data) 
                    msg = msg.strip()
                    # reply_data = {"reply":msg}
                    if(receive["message_type"]=="private"):
                        send_private_msg(receive["user_id"],msg)
                    elif (receive["message_type"]=="group"):
                        send_group_msg(receive["group_id"],msg)
                    # if(receive["message_type"]=="group"):
                    #     reply_data["at_sender"] = "false"
                    # return JsonResponse(reply_data)


                if (receive["message"].find('/dps')==0):
                    receive_msg = receive["message"].replace('/dpscheck','',1).strip()
                    receive_msg = receive_msg.replace('/dps','',1).strip()
                    boss_list = Boss.objects.all()
                    boss_obj = None
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
                        reply_data = {"reply":msg}  
                        return JsonResponse(reply_data) 
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
                        reply_data = {"reply":msg}  
                        return JsonResponse(reply_data) 
                    day = math.ceil((int(time.time())-boss.cn_add_time)/(24*3600))
                    tiles = DPSTile.objects.filter(boss=boss_obj,job=job_obj,day=day)
                    if(len(tiles)==0):
                        msg = "Boss:%s职业:%s第%s日的数据未抓取，请联系管理员抓取。"%(boss,job,day)
                        reply_data = {"reply":msg}  
                        return JsonResponse(reply_data) 
                    else:
                        tile = tiles[0]
                        if(receive_msg=="all"):
                            atk_dict = json.loads(tile.attack)
                            percentage_list = [10,25,50,75,95,99]
                            msg = "%s %s day#%s:\n"%(boss.cn_name,job.cn_name,day)
                            for perc in percentage_list:
                                msg += "%s%% : %.2f\n"%(perc,atk_dict[str(perc)])
                            msg = msg.strip()
                            reply_data = {"reply":msg}  
                            return JsonResponse(reply_data) 
                        try:
                            atk = float(receive_msg)
                            assert(atk > 0)
                        except:
                            msg = "DPS数值解析失败:%s"%(receive_msg)
                            reply_data = {"reply":msg}  
                            return JsonResponse(reply_data) 
                        atk_dict = json.loads(tile.attack)
                        percentage_list = [0,10,25,50,75,95,99]
                        atk_dict.update({"0":0})
                        print("atk_dict:"+json.dumps(atk_dict))
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
                        reply_data = {"reply":msg}  
                        return JsonResponse(reply_data) 


                #Private message
                if (receive["message_type"]=="private"):
                    if("[CQ:record,file=" in receive["message"]):
                        tmp = receive["message"]
                        tmp = tmp[tmp.find("file="):-1]
                        tmp = tmp.replace("file=","")
                        file_name = tmp.replace("]","")
                        jres = get_record(file_name)
                        if(jres["status"]=="ok"):
                            out_file = jres["data"]["file"]
                            record_url = QQPOST_URL+'/data/record/%s?access_token=2ASdOeYCOyp'%(out_file)
                            r = requests.get(url=record_url)
                            print("out_file:%s"%(jres["data"]["file"]))
                            if(r.status_code==200):
                                pass

                        else:
                            print("jres:%s"%(json.dumps(jres)))

                #Group Control Func
                if (receive["message_type"]=="group"):
                    group_id = receive["group_id"]
                    user_id = receive["user_id"]
                    keywords = ['/vote','/register_group','/set_welcome_msg','/add_custom_reply','/del_custom_reply','/welcome_demo','/set_repeat_ban','/disable_repeat_ban','/repeat','/left_reply','/set_ban','/ban']
                    if(receive["message"].find('/group_help')==0):
                        msg = "/register_group : 将此群注册到数据库\n/set_welcome_msg $msg: 设置欢迎语$msg\n/welcome_demo : 查看欢迎示例\n/add_custom_reply /$key $val : 添加自定义回复\n/del_custom_reply /$key : 删除自定义回复\n/set_repeat_ban $times : 设置复读机检测条数\n/disable_repeat_ban : 关闭复读机检测\n/repeat $times $prob : 以百分之$prob的概率复读超过$times的对话\n/left_reply : 查看本群剩余聊天条数\n/set_ban $cnt : 设置禁言投票基准为$cnt\n/ban $member $time : 投票将$member禁言$time分钟\n/ban $member : 给$member禁言投票"
                        msg = msg.strip()
                        reply_data = {"reply":msg}
                        if(receive["message_type"]=="group"):
                            reply_data["at_sender"] = "false"
                        return JsonResponse(reply_data)
                    if(receive["message"].find('/register_group')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        if(user_info["role"]!="owner"):
                            reply_data = {"reply":"仅群主有权限注册"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            group_list = QQGroup.objects.filter(group_id=group_id)
                            if len(group_list)==0:
                                group = QQGroup(group_id=group_id)
                                group.save()
                                reply_data = {"reply":"群%s注册成功"%(group_id)}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            else:
                                reply_data = {"reply":"本群%s已注册，请勿重复注册"%(group_id)}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)


                    group_list = QQGroup.objects.filter(group_id=group_id)
                    request_flag = False
                    for item in keywords:
                        if(receive["message"].find(item)==0):
                            request_flag = True
                            break
                    if len(group_list)==0:
                        if request_flag:
                            reply_data = {"reply":"本群%s未在数据库注册，请群主使用/register_group命令注册"%(group_id)}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            return
                    else:
                        group = group_list[0]
                        group.last_reply_time = time.time()
                        group.save()
                        if(time.time() <= group.ban_till):
                            return
                    if(receive["message"].find('/set_welcome_msg')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                            reply_data = {"reply":"仅群主与管理员有权限设置欢迎语"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            welcome_msg = receive["message"].replace("/set_welcome_msg","",1).strip()
                            group.welcome_msg = welcome_msg
                            group.save()
                            reply_data = {"reply":"欢迎语已设置成功，使用/welcome_demo查看欢迎示例"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                    if(receive["message"].find('/add_custom_reply')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                            reply_data = {"reply":"仅群主与管理员有权限设置自定义回复"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            ori_msg = receive["message"].replace("/add_custom_reply","",1).strip()
                            ori_msg = ori_msg.split(' ')
                            if(len(ori_msg)<2):
                                reply_data = {"reply":"自定义命令参数过少（/add_custom_reply /$key $val）"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            custom_key = ori_msg[0]
                            if(custom_key[0]!='/'):
                                reply_data = {"reply":"自定义命令以'/'开头"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            custom_value = html.unescape(ori_msg[1])

                            customs = CustomReply.objects.filter(group=group,key=custom_key)
                            if(len(customs)>0):
                                custom = customs[0]
                                custom.value = custom_value
                            else:
                                custom = CustomReply(group=group,key=custom_key,value=custom_value)
                            custom.save()
                            reply_data = {"reply":"自定义回复已添加成功，使用%s查看"%(custom_key)}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                    if(receive["message"].find('/del_custom_reply')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                            reply_data = {"reply":"仅群主与管理员有权限设置自定义回复"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            ori_msg = receive["message"].replace("/del_custom_reply","",1).strip()
                            ori_msg = ori_msg.split(' ')
                            if(len(ori_msg)<1):
                                reply_data = {"reply":"自定义回复参数过少（/del_custom_reply /$key）"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            custom_key = ori_msg[0]
                            if(custom_key[0]!='/'):
                                reply_data = {"reply":"自定义回复命令以'/'开头"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            custom = CustomReply.objects.filter(group=group,key=custom_key)
                            if(len(custom)==0):
                                reply_data = {"reply":"不存在%s为命令的自定义回复"%(custom_key)}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            else:
                                custom[0].delete()
                            reply_data = {"reply":"自定义回复已删除成功，使用%s查看"%(custom_key)}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                    if(receive["message"].find('/welcome_demo')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        group_list = QQGroup.objects.filter(group_id=group_id)
                        print("welcome_demo")
                        group = group_list[0]
                        reply_data = {"reply":group.welcome_msg}
                        return JsonResponse(reply_data)                            
                    if(receive["message"].find('/set_repeat_ban')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        if(user_info["role"]!="owner" ):
                            reply_data = {"reply":"仅群主有权限开启复读机检测系统"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            ori_msg = receive["message"].replace("/set_repeat_ban","",1).strip()
                            ori_msg = ori_msg.split(' ')
                            if(len(ori_msg)<1):
                                reply_data = {"reply":"请设置复读机一分钟内的最大条数（/add_custom_reply $times）"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            try:
                                group.repeat_ban = max(int(ori_msg[0]),2)
                            except Exception as e:
                                group.repeat_ban = 10
                            group.save()
                            reply_data = {"reply":"复读机监控系统已启动，检测值为%s/min"%(group.repeat_ban)}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                    if(receive["message"].find('/disable_repeat_ban')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                            reply_data = {"reply":"仅群主与管理员有权限关闭复读机检测系统"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            group = group_list[0]
                            group.repeat_ban = -1
                            group.save()
                            reply_data = {"reply":"复读机监控系统已关闭"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                    if(receive["message"].find('/repeat')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        if(user_info["role"]=="owner" or user_info["role"]=="admin" ):
                            reply_data = {"reply":"仅非群主与管理员有权限开启复读机系统"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            ori_msg = receive["message"].replace("/repeat","",1).strip()
                            ori_msg = ori_msg.split(' ')
                            if(len(ori_msg)<2):
                                reply_data = {"reply":"请复读机条数与复读概率（/repeat $times $prob）"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            try:
                                group.repeat_length = max(int(ori_msg[0]),2)
                                group.repeat_prob = min(int(ori_msg[1]),50)
                            except Exception as e:
                                group.repeat_length = 2
                                group.repeat_prob = 50
                            group.save()
                            reply_data = {"reply":"复读机系统已启动，复读概率为%s/min后的%s%%"%(group.repeat_length,group.repeat_prob)}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                    if(receive["message"].find('/left_reply')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        group_list = QQGroup.objects.filter(group_id=group_id)
                        group = group_list[0]
                        reply_data = {"reply":"本群剩余%s条獭獭聊天限额"%(group.left_reply_cnt)}
                        reply_data["at_sender"] = "false"
                        return JsonResponse(reply_data)
                    if(receive["message"].find('/set_ban')==0):
                        user_info = get_group_member_info(group_id,user_id)
                        if(user_info["role"]!="owner" and user_info["role"]!="admin" ):
                            reply_data = {"reply":"仅群主与管理员有权限设置禁言投票"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        else:
                            ban_cnt = receive["message"].replace("/set_ban","",1).strip()
                            try:
                                group.ban_cnt = max(int(ban_cnt),2)
                                if(int(ban_cnt)==-1):
                                    group.ban_cnt = -1
                            except:
                                group.ban_cnt = 10
                            group.save()
                            reply_data = {"reply":"禁言投票基准被设置为%s"%(group.ban_cnt)}
                            if(group.ban_cnt==-1):
                                reply_data = {"reply":"禁言投票已关闭"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                    if(receive["message"].find('/ban')==0):
                        if(group.ban_cnt<=0):
                            reply_data = {"reply":"本群未开放禁言投票功能"}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
                        receive_msg = receive["message"].replace("/ban","",1).strip()
                        msg_list = receive_msg.split(' ')
                        if(len(msg_list)>=1):
                            pattern = "[CQ:at,qq="
                            qq_str = msg_list[0]
                            if(qq_str.find(pattern)>=0):
                                qq = qq_str[qq_str.find(pattern)+len(pattern):qq_str.find("]")]
                            else:
                                qq = qq_str
                            if not qq.isdecimal():
                                reply_data = {"reply":"请艾特某人或输入其QQ号码"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            mems = Member.objects.filter(user_id=qq,group=group,timestamp__gt=time.time()-3600)
                            del_mems = Member.objects.filter(user_id=qq,group=group,timestamp__lt=time.time()-3600)
                            for item in del_mems:
                                item.delete()
                            if(len(msg_list)==1):
                                if(len(mems)==0):
                                    reply_data = {"reply":"不存在针对 [CQ:at,qq=%s] 的禁言投票，请输入\"/ban %s $time\"开始时长为$time分钟的禁言投票"%(qq,qq)}
                                    reply_data["at_sender"] = "false"
                                    return JsonResponse(reply_data)
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
                                        user_info = get_group_member_info(group.group_id,mem.user_id)
                                        voted_msg = ""
                                        for item in vtlist["voted_by"]:
                                            voted_msg += "[CQ:at,qq=%s] "%(item)
                                        msg = "被%s投票禁言%s分钟"%(voted_msg, mem.ban_time)
                                        msg += " 复仇请输入/revenge"
                                        if(user_info["role"]=="owner"):
                                            msg = "虽然你是狗群主獭獭无法禁言，但是也被群友投票禁言，请闭嘴%s分钟[CQ:face,id=14]"%(mem.ban_time)
                                        if(user_info["role"]=="admin"):
                                            msg = "虽然你是狗管理獭獭无法禁言，但是也被群友投票禁言，请闭嘴%s分钟[CQ:face,id=14]"%(mem.ban_time)
                                        if(str(mem.user_id) == str(receive["self_id"])):
                                            msg = "%s竟然禁言了可爱的獭獭[CQ:face,id=111][CQ:face,id=111]好吧我闭嘴%s分钟[CQ:face,id=14]"%(voted_msg, mem.ban_time)
                                            group.ban_till = time.time()+int(mem.ban_time)*60
                                            group.save()
                                        else:
                                            group_ban(group.group_id,mem.user_id,int(mem.ban_time)*60)
                                            rev = Revenge(user_id=mem.user_id,group=group)
                                            rev.timestamp = time.time()
                                            rev.vote_list = mem.vote_list
                                            rev.ban_time = mem.ban_time
                                            rev.save()
                                        mem.delete()
                                        send_group_msg(group_id,msg,mem.user_id)
                                    else:
                                        reply_data = {"reply":"[CQ:at,qq=%s] 时长为%s分钟的禁言投票，目前进度：%s/%s"%(mem.user_id,mem.ban_time,len(vtlist["voted_by"]),group.ban_cnt)}
                                        reply_data["at_sender"] = "false"
                                        return JsonResponse(reply_data)
                            elif(len(msg_list)==2):
                                if not msg_list[1].isdecimal():
                                    reply_data = {"reply":"禁言时长无效"}
                                    reply_data["at_sender"] = "false"
                                    return JsonResponse(reply_data)
                                if(len(mems)==0):
                                    default_ban_time = 2
                                    mem = Member(user_id=qq,group=group,ban_time=min(int(msg_list[1]),default_ban_time))
                                    if(str(mem.user_id)==str(user_id)):
                                        mem.ban_time = max(mem.ban_time,default_ban_time)
                                    vtlist = json.loads(mem.vote_list)
                                    vtlist["voted_by"] = []
                                    vtlist["voted_by"].append(str(receive["user_id"]))
                                    vtlist["voted_by"] = list(set(vtlist["voted_by"]))
                                    mem.vote_list = json.dumps(vtlist)
                                    mem.timestamp = time.time()
                                    mem.save()
                                    reply_data = {"reply":"开始了针对 [CQ:at,qq=%s] 时长为%s分钟的禁言投票，投票请发送/ban %s"%(qq,mem.ban_time,qq)}
                                    reply_data["at_sender"] = "false"
                                    return JsonResponse(reply_data)
                                else:
                                    mem = mems[0]
                                    reply_data = {"reply":"已存在针对 [CQ:at,qq=%s] 时长为%s分钟的禁言投票，投票请发送/ban %s"%(qq,mem.ban_time,qq)}
                                    reply_data["at_sender"] = "false"
                                    return JsonResponse(reply_data)
                    

                    if(receive["message"]=='/revenge' or receive["message"]=="/revenge_confirm"):
                        print("here")
                        revs = Revenge.objects.filter(user_id=user_id,group=group,timestamp__gt=time.time()-3600)
                        del_revs = Revenge.objects.filter(user_id=user_id,group=group,timestamp__lt=time.time()-3600)
                        for item in del_revs:
                            item.delete()
                        if(len(revs)>0):
                            rev = revs[0]
                            qq_list = (json.loads(rev.vote_list))["voted_by"]
                            msg = "[CQ:at,qq=%s]将要与"%(user_id)
                            for item in qq_list:
                                msg += "[CQ:at,qq=%s] "%(item)
                            msg += "展开复仇,您将被禁言%s分钟,其余众人将被禁言%s分钟，确认请发送/revenge_confirm"%(int(rev.ban_time)*(len(qq_list)),rev.ban_time)
                            if(receive["message"]=="/revenge_confirm"):
                                for item in qq_list:
                                    if(str(item)==str(user_id)):
                                        continue
                                    group_ban(group_id,item,int(rev.ban_time)*60)
                                    time.sleep(1)
                                time.sleep(1)
                                group_ban(group_id,user_id,int(rev.ban_time)*(len(qq_list))*60)
                                msg = "[CQ:at,qq=%s]复仇完毕，嘻嘻嘻。"%(user_id)
                                rev.delete()
                            send_group_msg(group_id,msg)

                        else:
                            reply_data = {"reply":"不存在关于您的复仇机会。"}
                            return JsonResponse(reply_data)

                    if (receive["message"].find('/vote')==0):
                        receive_msg = receive["message"].replace('/vote','',1).strip()
                        if receive_msg=="list":
                            vs = Vote.objects.filter(group=group)
                            msg = ""
                            for item in vs:
                                starttime_str = time.strftime(TIMEFORMAT,time.localtime(item.starttime))
                                endtime_str = time.strftime(TIMEFORMAT,time.localtime(item.endtime))
                                msg = msg + "#%s:%s %s -- %s\n"%(item.id,item.name,starttime_str,endtime_str)
                            msg = msg.strip()
                            reply_data = {"reply":msg}
                            reply_data["at_sender"] = "false"
                            return JsonResponse(reply_data)
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
                                reply_data = {"reply":"不存在#%s号投票"%(vote_id)}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            else:
                                receive_msg = receive_msg.replace(vote_id_str,"",1).strip()
                                if(receive_msg.find("check")==0 or receive_msg==""):
                                    vote = votes[0]
                                    vote_json = json.loads(vote.vote)
                                    sum_list = [{"qq":item[0],"tot":len(item[1]["voted_by"])} for item in vote_json.items()]
                                    print(sum_list)
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
                                        reply_data = {"reply":"请艾特某人进行投票"}
                                        reply_data["at_sender"] = "false"
                                        return JsonResponse(reply_data)
                                    vote = votes[0]
                                    if(time.time()<vote.starttime):
                                        msg = "投票 #%s:%s 未开始。"%(vote.id,vote.name)
                                        reply_data = {"reply":msg}
                                        return JsonResponse(reply_data)
                                    if(time.time()>vote.endtime):
                                        msg = "投票 #%s:%s 已结束。"%(vote.id,vote.name)
                                        reply_data = {"reply":msg}
                                        return JsonResponse(reply_data)
                                    vote_json = json.loads(vote.vote)
                                    can_vote = True
                                    for (k,v) in vote_json.items():
                                        # print(v)
                                        # print(str(user_id))
                                        # print(str(user_id) in v)
                                        if(str(user_id) in v["voted_by"]):
                                            msg = "[CQ:at,qq=%s]在 #%s:%s 中已投票，不可重复投票。"%(user_id,vote.id,vote.name)
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
                                        msg = "[CQ:at,qq=%s]在 #%s:%s 中给[CQ:at,qq=%s]投票成功，目前票数%s。"%(user_id,vote.id,vote.name,qq,len(vote_list))
                        else:
                            msg = "/vote list: 群内投票ID与内容\n/vote #$id check : 投票$id的目前结果\n/vote #$id @$member : 通过艾特给某人投票"
                        msg = msg.strip()
                        reply_data = {"reply":msg}
                        if(receive["message_type"]=="group"):
                            reply_data["at_sender"] = "false"
                        return JsonResponse(reply_data)


                    if len(group_list)>0:
                        group = group_list[0]
                        custom_replys = CustomReply.objects.filter(group=group)
                        #custom replys
                        for item in custom_replys:
                            if(receive["message"].find(item.key)==0):
                                reply_data = {"reply":item.value}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                        #repeat_ban & repeat
                        chats = ChatMessage.objects.filter(group=group,message=receive["message"].strip(),timestamp__gt=time.time()-60)
                        del_chats = ChatMessage.objects.filter(group=group,timestamp__lt=time.time()-60)
                        for item in del_chats:
                            item.delete()
                        if(len(chats)>0):
                            chat = chats[0]
                            chat.times = chat.times+1
                            chat.save()
                            if(group.repeat_ban>0 and chat.times>=group.repeat_ban):
                                group_ban(group.group_id,receive["user_id"])
                                user_info = get_group_member_info(group.group_id,receive["user_id"])
                                msg = "抓到你了，复读姬！╭(╯^╰)╮口球一分钟！"
                                if(user_info["role"]=="owner"):
                                    msg = "虽然你是狗群主獭獭无法禁言，但是也触发了复读机检测系统，请闭嘴一分钟[CQ:face,id=14]"
                                if(user_info["role"]=="admin"):
                                    msg = "虽然你是狗管理獭獭无法禁言，但是也触发了复读机检测系统，请闭嘴一分钟[CQ:face,id=14]"
                                send_group_msg(group_id,msg,receive["user_id"])
                                delete_msg(receive["message_id"])
                            if(group.repeat_length>=1 and group.repeat_prob>0 and chat.times>=group.repeat_length and (not chat.repeated)):
                                if(random.randint(1,100)<=group.repeat_prob):
                                    send_group_msg(group_id,chat.message)
                                    chat.repeated = True
                                    chat.save()
                        else:
                            if(group.repeat_ban>0 or (group.repeat_length>=1 and group.repeat_prob>0) ):
                                if(receive["self_id"]!=receive["user_id"]):
                                    chat = ChatMessage(group=group,message=receive["message"].strip(),timestamp=time.time())
                                    chat.save()
                        #tuling chatbot
                        if("[CQ:at,qq=%s]"%(receive["self_id"]) in receive["message"]):
                            if(group.left_reply_cnt <= 0):
                                reply_data = {"reply":"聊天限额已耗尽，请等待回复。"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            if(str(receive["user_id"]) in QQBOT_LIST):
                                reply_data = {"reply":"本獭獭不理机器人。"}
                                reply_data["at_sender"] = "false"
                                return JsonResponse(reply_data)
                            print("Tuling reply")
                            receive_msg = receive["message"]
                            receive_msg = receive_msg.replace("[CQ:at,qq=%s]"%(receive["self_id"]),"")
                            tuling_data = {}
                            tuling_data["reqType"] = 0  #Text
                            tuling_data["perception"] = {"inputText": {"text": receive_msg}}
                            tuling_data["userInfo"] = {"apiKey": TULING_API_KEY, "userId": receive["user_id"], "groupId": group.group_id}
                            r = requests.post(url=TULING_API_URL,data=json.dumps(tuling_data),timeout=3)
                            tuling_reply = json.loads(r.text)
                            print("tuling reply:%s"%(r.text))
                            tuling_results = tuling_reply["results"]
                            msg = ""
                            for item in tuling_results:
                                if(item["resultType"]=="text"):
                                    msg += item["values"]["text"]
                            msg = msg.replace("小主人","小光呆")
                            send_group_msg(group_id,msg,receive["user_id"])
                            group.left_reply_cnt = max(group.left_reply_cnt - 1, 0)
                            group.save()
                        #baidu image censor
                        # if("[CQ:image" in receive["message"]):
                        #     print("censoring img")
                        #     image_censor(receive)

            if (receive["post_type"] == "request"):
                if (receive["request_type"] == "friend"):   #Add Friend
                    qq = receive["user_id"]
                    reqmsg = receive["message"]
                    reqmsg = str(reqmsg).upper()
                    reply_data = {"approve": "FFXIV" in reqmsg or "FF14" in reqmsg}
                    reply_data = {"approve":False,"reason":"好友过多，考虑服务器负荷暂时拒绝新的好友请求。"}
                    return JsonResponse(reply_data)
                if (receive["request_type"] == "group" and receive["sub_type"] == "invite"):    #Add Group
                    reply_data = {"approve":False,"reason":"群过多，考虑服务器负荷暂时拒绝新的进群邀请。"}
                    print(reply_data)
                    return JsonResponse(reply_data)
            if (receive["post_type"] == "event"):
                if (receive["event"] == "group_increase"):
                    group_id = receive["group_id"]
                    user_id = receive["user_id"]
                    group_list = QQGroup.objects.filter(group_id=group_id)
                    if len(group_list)>0:
                        group = group_list[0]
                        msg = group.welcome_msg.strip()
                        if(msg!=""):
                            send_group_msg(group_id,msg,user_id)
                            # reply_data = {"reply":msg}
                            # return JsonResponse(reply_data)
        return HttpResponse(status=204)
    except Exception as e:
        traceback.print_exc() 
