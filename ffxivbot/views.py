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
import requests
import base64
import random,sys
import traceback  
import codecs
import hmac
from bs4 import BeautifulSoup
import urllib.parse
# Create your views here.

#Base Constant
QQPOST_URL = 'http://127.0.0.1:5700'
ACCESS_TOKEN = "ACCESS_TOKEN"
SECRET_KEY = "SECRET_KEY"

#random.org
RANDOMORG_TOKEN = "RANDOMORG_KEY"

#whatanime.ga
WHATANIME_TOKEN = "WHATANIME_TOKEN"
WHATANIME_API_URL = "https://whatanime.ga/api/search?token="+WHATANIME_TOKEN

#ff14.huijiwiki.com
FF14WIKI_BASE_URL = "https://ff14.huijiwiki.com"
FF14WIKI_API_URL = "https://cdn.huijiwiki.com/ff14/api.php"

#sorry API
SORRY_BASE_URL = "https://sorry.xuty.tk/"

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
        s=requests.post(url=QQPOST_URL+'/send_private_msg?access_token='+ACCESS_TOKEN,data=jdata,timeout=10)
    elif(receive["message_type"]=="group"):
        jdata = {"group_id":receive["group_id"],"message":"[CQ:at,qq=%s]\n"%(receive["user_id"])+msg}
        s=requests.post(url=QQPOST_URL+'/send_group_msg?access_token=2ASdOeYCOyp',data=jdata,timeout=10)





@csrf_exempt
def qqpost(req):
    try:
        receive = json.loads(req.body.decode())
        sig = hmac.new(b'pinkpink', req.body, 'sha1').hexdigest()
        received_sig = req.META.get("HTTP_X_SIGNATURE","unknow")[len('sha1='):]
        if(sig == received_sig):
            if (receive["post_type"] == "message"):
                if (receive["message"] == '/cat'):
                    reply_data = {"reply":[{"type":"image","data":{"file":"cat/%s.jpg"%(random.randint(0,750))}}],"at_sender":"false"}
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
                if (receive["message"].find('/anime')==0):
                    print("anime_msg:%s"%(receive["message"]))
                    qq = int(receive["user_id"])
                    if(receive["message"] == '/anime'):
                        pass
                    elif ("CQ" in receive["message"] and "url=" in receive["message"]):
                        reply_data = whatanime(receive)
                if (receive["message"].find('/random')==0):
                    min_lim = 1
                    max_lim = 999
                    try:
                        num = int(receive["message"].replace("/random",""))
                    except:
                        num = 1
                    num = min(num,6)
                    post_data = {"jsonrpc":"2.0","method":"generateIntegers","params":{"apiKey":RANDOMORG_TOKEN,"n":num,"min":min_lim,"max":max_lim,"replacement":"true"},"id":1}
                    try:
                        s=requests.post(url='https://api.random.org/json-rpc/1/invoke',data=json.dumps(post_data),timeout=0.5)
                        res_jdata = json.loads(s.text)
                        if ("error" in res_jdata):
                            msg = res_jdata["error"]["message"]
                        else:
                            msg = ""
                            num_list = res_jdata["result"]["random"]["data"]
                            for item in num_list:
                                msg = msg + "%s "%(item)
                            msg = msg.strip()
                    except Exception as e:
                        traceback.print_exc()
                        msg = str(random.randint(1,1000))+"(pseudo-random)"
                    reply_data = {"reply":"[CQ:at,qq=%s]掷出了"%(receive["user_id"])+msg+"点！","at_sender":"false"}
                    print("reply_data:%s"%(reply_data))
                    return JsonResponse(reply_data)
                if (receive["message"].find('/gif')==0):
                    sorry_dict = {"sorry":"好啊|就算你是一流工程师|就算你出报告再完美|我叫你改报告你就要改|毕竟我是客户|客户了不起啊|sorry 客户真的了不起|以后叫他天天改报告|天天改 天天改","wangjingze":"我就是饿死|死外边 从这跳下去|也不会吃你们一点东西|真香","jinkela":"金坷垃好处都有啥|谁说对了就给他|肥料掺了金坷垃|不流失 不蒸发 零浪费|肥料掺了金坷垃|能吸收两米下的氮磷钾","marmot":"啊~|啊~~~","dagong":"没有钱啊 肯定要做的啊|不做的话没有钱用|那你不会去打工啊|有手有脚的|打工是不可能打工的|这辈子不可能打工的","diandongche":"戴帽子的首先进里边去|开始拿剪刀出来 拿那个手机|手机上有电筒 用手机照射|寻找那个比较新的电动车|六月六号 两名男子再次出现|民警立即将两人抓获"}
                    sorry_name = {"sorry":"为所欲为","wangjingze":"王境泽","jinkela":"金坷垃","marmot":"土拨鼠","dagong":"窃格瓦拉","diandongche":"偷电动车"}
                    receive_msg = receive["message"].replace('/gif','').strip()
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
                            receive_msg = receive_msg.replace(now_template,"").strip()
                            if(receive_msg=="example"):
                                msg = sorry_dict[now_template]
                            else:
                                msgs = receive_msg.split('|')
                                if(len(msgs)==0):
                                    msg = "至少包含一条字幕消息"
                                else:
                                    cnt = 0
                                    gen_data = {}
                                    for sentence in msgs:
                                        gen_data[str(cnt)] = sentence
                                        print("sentence#%s:%s"%(cnt,sentence))
                                        cnt += 1
                                    print("gen_data:%s"%(json.dumps(gen_data)))
                                    url = SORRY_BASE_URL + "api/%s/make"%(now_template)
                                    try:
                                        s = requests.post(url=url,data=json.dumps(gen_data),timeout=2)
                                        img_url = SORRY_BASE_URL + s.text
                                        print("img_url:%s"%(img_url))
                                        msg = '[CQ:image,cache=0,file='+img_url+']'
                                    except Exception as e:
                                        msg = "SORRY API ERROR:%s"%(e)
                                        print(msg)
                                        reply_data = {"reply":msg}  
                                        return JsonResponse(reply_data) 
                    msg = msg.strip()
                    reply_data = {"reply":msg}
                    if(receive["message_type"]=="group"):
                        reply_data["at_sender"] = "false"
                    return JsonResponse(reply_data)
            if (receive["post_type"] == "request"):
                if (receive["request_type"] == "friend"):   #Add Friend
                    qq = receive["user_id"]
                    reply_data = {"approve": "FFXIV" in receive["message"]}
                    return JsonResponse(reply_data)
                if (receive["request_type"] == "group" and receive["sub_type"] == "invite"):    #Add Group
                    reply_data = {"approve":True}
                    return JsonResponse(reply_data)
        return HttpResponse(status=204)
    except Exception as e:
        traceback.print_exc() 
