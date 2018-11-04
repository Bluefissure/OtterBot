# -*- coding: utf-8 -*-
from django.shortcuts import render, Http404, HttpResponseRedirect
from django.contrib import auth
from django.contrib.auth.decorators import login_required
from django.template import Context, RequestContext, loader
from django.template.context_processors import csrf
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
from channels.layers import get_channel_layer 
from asgiref.sync import async_to_sync
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
from websocket import create_connection
def ren2res(template, req, dict={},post_token=True):
	dict.update({'user': False})
	dict.update(csrf(req))
	response = render(req, template, dict)
	return response

# Create your views here.

def tata(req):
	if req.is_ajax() and req.method=='POST':
		dict = {"response":"No response."}
		optype = req.POST.get("optype")
		if (optype=="add_or_update_bot"):
			botName = req.POST.get("botName")
			botID = req.POST.get("botID")
			ownerID = req.POST.get("ownerID")
			accessToken = req.POST.get("accessToken")
			tulingToken = req.POST.get("tulingToken")
			autoFriend = req.POST.get("autoFriend")
			autoInvite = req.POST.get("autoInvite")
			print("{},{},{},{},{},{},{}".format(botName,botID,ownerID,accessToken,tulingToken,autoFriend,autoInvite))
			if(len(botName)<2):
				dict = {"response":"error","msg":"机器人昵称太短"}
				return JsonResponse(dict)
			elif(len(accessToken)<5):
				dict = {"response":"error","msg":"Access Token太短"}
				return JsonResponse(dict)
			elif(len(ownerID.strip())==0):
				dict = {"response":"error","msg":"领养者不能为空"}
				return JsonResponse(dict)
			bots = QQBot.objects.filter(user_id=botID)
			bot = None
			if(len(bots)==0):
				bot = QQBot(user_id=botID,access_token=accessToken)
				bot_created = True
			else:
				if(bots[0].access_token!=accessToken):
					dict = {"response":"error","msg":"Token错误，请确认后重试。"}
					return JsonResponse(dict)
				else:
					bot = bots[0]
					bot_created = False
			if bot:
				bot.name = botName
				bot.owner_id = ownerID
				bot.tuling_token = tulingToken
				bot.auto_accept_friend = autoFriend and "true" in autoFriend
				bot.auto_accept_invite = autoInvite and "true" in autoInvite
				if(len(QQBot.objects.all())>=1 and bot_created):
					dict = {"response":"error","msg":"机器人总数过多，请稍后再试"}
					return JsonResponse(dict)
				bot.save()
				if(bot_created):
					dict = {"response":"success","msg":"{}({})添加成功，Token为:".format(bot.name,bot.user_id),"token":bot.access_token}
				else:
					dict = {"response":"success","msg":"{}({})更新成功，Token为:".format(bot.name,bot.user_id),"token":bot.access_token}
			return JsonResponse(dict)
		else:
			id = req.POST.get("id")
			token = req.POST.get("token")
			try:
				bot = QQBot.objects.get(id=id,access_token=token)
			except Exception as e:
				if "QQBot matching query does not exist" in str(e):
					dict = {"response":"error","msg":"Token错误，请确认后重试。"}
				else:
					dict = {"response":"error","msg":str(e)}
				return JsonResponse(dict)
			if(optype=="switch_public"):
				bot.public = not bot.public
				bot.save()
				dict["response"] = "success"
			elif(optype=="del_bot"):
				bot.delete()
				dict["response"] = "success"
			elif(optype=="download_conf"):
				response = HttpResponse(content_type='application/octet-stream')
				response['Content-Disposition'] = 'attachment; filename="{}.json"'.format(bot.user_id)
				bot_conf = json.loads('{"host":"0.0.0.0","port":5700,"use_http":false,"ws_host":"0.0.0.0","ws_port":6700,"use_ws":false,"ws_reverse_api_url":"ws://111.231.102.248/ws_api/","ws_reverse_event_url":"ws://111.231.102.248/ws_event/","use_ws_reverse":"yes","ws_reverse_reconnect_interval":5000,"ws_reverse_reconnect_on_code_1000":"yes","post_url":"","access_token":"SECRET","secret":"","post_message_format":"string","serve_data_files":false,"update_source":"github","update_channel":"stable","auto_check_update":false,"auto_perform_update":false,"thread_pool_size":4,"server_thread_pool_size":1,"show_log_console":false,"enable_backward_compatibility":true}')
				bot_conf["secret"] = bot.access_token
				response.write(json.dumps(bot_conf,indent=4))
				return response
			print(optype)
			print(req.POST)
		return JsonResponse(dict)

	bots = QQBot.objects.all()
	bot_list = []
	for bot in bots:
		bb = {}
		version_info = json.loads(bot.version_info)
		coolq_edition = version_info["coolq_edition"] if version_info and "coolq_edition" in version_info.keys() else ""
		if coolq_edition != "":
			coolq_edition = coolq_edition[0].upper()+coolq_edition[1:]
		friend_list = json.loads(bot.friend_list)
		friend_num = len(friend_list["friends"]) if friend_list and "friends" in friend_list.keys() else "-1"
		group_list = json.loads(bot.group_list)
		group_num = len(group_list) 
		bb["name"] = bot.name 
		if bot.public:
			bb["user_id"] = bot.user_id
		else:
			mid = len(bot.user_id)//2
			user_id = bot.user_id[:mid-2]+"*"*4+bot.user_id[mid+2:]
			bb["user_id"] = user_id
		bb["group_num"] = group_num
		bb["friend_num"] = friend_num
		bb["coolq_edition"] = coolq_edition
		bb["owner_id"] = bot.owner_id
		bb["online"] = time.time() - bot.api_time < 300
		bb["id"] = bot.id
		bb["public"] = bot.public
		bb["autoinvite"] = bot.auto_accept_invite
		bb["autofriend"] = bot.auto_accept_friend
		bot_list.append(bb)
	return ren2res("pages/tables/data.html",req,{"bots":bot_list})


def quest(req):
	if req.is_ajax() and req.method=='POST':
		dict = {"response":"No response."}
		optype = req.POST.get("optype")
		if(optype=="search_quest"):
			max_iter = req.POST.get("max_iter")
			main_quest = req.POST.get("main_quest")
			main_quest = main_quest and "true" in main_quest
			sub_quest = req.POST.get("sub_quest")
			sub_quest = sub_quest and "true" in sub_quest
			start_quest = req.POST.get("start_quest")
			start_quest = PlotQuest.objects.filter(name=start_quest)
			start_quest = start_quest[0] if len(start_quest)>0 else None
			end_quest = req.POST.get("end_quest")
			end_quest = PlotQuest.objects.filter(name=end_quest)
			end_quest = end_quest[0] if len(end_quest)>0 else None
			max_iter = req.POST.get("max_iter")
			print("main_quest:{}".format(main_quest))
			print("sub_quest:{}".format(sub_quest))
			quest_dict = {}
			tmp_edge_list = []
			edge_list = []
			if(not start_quest and not end_quest):
				dict["response"] = "找不到对应任务"
			elif(start_quest and end_quest):
				dict["response"] = "TODO: Double Quest Search"
				pass
			else:
				single_quest = start_quest or end_quest
				search_list = []
				search_iter = 0
				search_list.append((single_quest, 1, 1))
				search_list.append((single_quest, 2, 1))
				if ("主线" in single_quest.category and not main_quest) or (not "主线" in single_quest.category and not sub_quest):
					dict["response"] = "查询任务类别与所选类别不符，清选择正确的类别。"
					return JsonResponse(dict)	
				done_cnt = 0
				tot_cnt = 0
				while(len(search_list)>0 and search_iter<=min(int(max_iter),1000)):
					try:
						(now_quest, direction, search_iter) = search_list[0]
						search_list = search_list[1:]
						if "主线" in now_quest.category:
							if(not main_quest):
								continue
						elif not sub_quest:
							continue
						if(direction==2):
							done_cnt += 1
						now_quest_dict = {
							"description":now_quest.category,
							"startnpc":now_quest.startnpc,
							"endnpc":now_quest.endnpc,
						}
						if now_quest.name not in quest_dict.keys():
							quest_dict[now_quest.name] = now_quest_dict
						else:
							if(now_quest.name!=single_quest.name):
								continue
						if not now_quest.endpoint:
							if direction==1:
								for quest in now_quest.suf_quests.all():
									if(quest.name not in quest_dict.keys()):
										search_list.append((quest,1,search_iter+1))
									edge = {"from":now_quest.name, "to":quest.name, }
									if edge not in edge_list:
										tmp_edge_list.append(edge)
						if not now_quest.endpoint or (now_quest.endpoint and now_quest.name==single_quest.name):
							if direction==2:
								for quest in now_quest.pre_quests.all():
									if(quest.name not in quest_dict.keys()):
										search_list.append((quest,2,search_iter+1))
									edge = {"from":quest.name, "to":now_quest.name, }
									if edge not in edge_list:
										tmp_edge_list.append(edge)
					except Exception as e:
						print(e)
				for edge in tmp_edge_list:
					if edge["from"] in quest_dict.keys() and edge["to"] in quest_dict.keys():
						edge_list.append(edge)
				quest_dict[single_quest.name]["style"] = "fill: #7f7"
				tot_cnt = len(quest_dict.keys())
				perc = done_cnt/tot_cnt*100
				perc = min(100, perc)
				perc = max(0, perc)
				dict["percentage"] = perc
				dict["quest_dict"] = quest_dict
				dict["quest_dict"] = quest_dict
				dict["edge_list"] = edge_list
				dict["response"] = "success"
		return JsonResponse(dict)	
	return ren2res("quest.html",req,{})

def get_nm_id(tracker, nm_name):
	if(tracker=="ffxiv-eureka"):
		name_id = {
			"科里多仙人刺":1,
			"常风领主":2,
			"忒勒斯":3,
			"常风皇帝":4,
			"卡利斯托":5,
			"群偶":6,
			"哲罕南":7,
			"阿米特":8,
			"盖因":9,
			"庞巴德":10,
			"塞尔凯特":11,
			"武断魔花茱莉卡":12,
			"白骑士":13,
			"波吕斐摩斯":14,
			"阔步西牟鸟":15,
			"极其危险物质":16,
			"法夫纳":17,
			"阿玛洛克":18,
			"拉玛什图":19,
			"帕祖祖":20,
		}
		for (k,v) in name_id.items():
			if(k in nm_name):
				return v
	return -1
@csrf_exempt
def api(req):
	if req.method=="POST":
		tracker = req.GET.get('tracker')
		print("tracker:{}".format(tracker))
		if(tracker):
			if(tracker=="ffxiv-eureka"):
				instance = req.GET.get('instance')
				password = req.GET.get('password')
				print("ffxiv-eureka {}:{}".format(instance,password))
				if(instance and password):
					nm_name = req.POST.get('text')

					if(nm_name):
						nm_id = get_nm_id("ffxiv-eureka",nm_name)
						print("nm_name:{} id:{}".format(nm_name,nm_id))
						if(nm_id > 0):
							print("nm_name:{} nm_id:{}".format(nm_name,nm_id))
							ws = create_connection("wss://ffxiv-eureka.com/socket/websocket?vsn=2.0.0")
							msg = '["1","1","instance:{}","phx_join",{{"password":"{}"}}]'.format(instance,password)
							print(msg)
							ws.send(msg)
							msg = '["1","2","instance:{}","set_kill_time",{{"id":{},"time":{}}}]'.format(instance,nm_id,int(time.time()*1000))
							print(msg)
							ws.send(msg)
							ws.close()
							return HttpResponse("OK",status=200)
					else:
						print("no nm_name")
			elif(tracker=="qq"):
				bot_qq = req.GET.get('bot_qq')
				qq = req.GET.get('qq')
				token = req.GET.get('token')
				print("bot: {} qq:{} token:{}".format(bot_qq, qq, token))
				if(bot_qq and qq and token):
					bot = None
					qquser = None
					try:
						bot = QQBot.objects.get(user_id=bot_qq)
					except QQBot.DoesNotExist:
						print("bot {} does not exist".format(bot_qq))
					try:
						qquser = QQUser.objects.get(user_id=qq, bot_token=token)
					except QQUser.DoesNotExist:
						print("qquser {}:{} auth fail".format(qq, token))
					if bot and qquser:
						channel_layer = get_channel_layer()
						msg = req.POST.get('text')
						jdata = {
							"action":"send_private_msg",
							"params":{"user_id":qquser.user_id,"message":msg},
							"echo":"",
						}
						async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})
						return HttpResponse("OK",status=200)


	return HttpResponse(status=404)


@csrf_exempt
def qqpost(req):
	pass
