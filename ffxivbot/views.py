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
def ren2res(template, req, dict={},post_token=True):
    dict.update({'user': False})
    dict.update(csrf(req))
    response = render(req, template, dict)
    return response

# Create your views here.

def index(req):
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
				if(len(QQBot.objects.all())>=100):
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
		bb["online"] = time.time() - bot.online_time < 60
		bb["id"] = bot.id
		bb["public"] = bot.public
		bot_list.append(bb)
	return ren2res("pages/tables/data.html",req,{"bots":bot_list})

@csrf_exempt
def qqpost(req):
    pass
