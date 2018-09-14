#!/usr/bin/env python3
import random
import sys
import os
import codecs
import urllib
import base64
sys.path.append('/home/ubuntu/FFXIVBOT/')
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIVBOT.settings'
from FFXIVBOT import settings
import django
import string
import requests
import time
import json
import re
from django.db import connection, connections
django.setup()
from ffxivbot.models import *
from bs4 import BeautifulSoup
import urllib
import traceback
sys.setrecursionlimit(10000) # solve recursive stack overflow
global to_crawl_list
to_crawl_list = []

def progress(percent,width=50):
	if percent >= 100:
		percent=100
	show_str=('[%%-%ds]' %width) %(int(width * percent/100)*"#") 
	print('\r%s %d%%' %(show_str,percent),end='')

def search_quest(url,direction=1):
	r = requests.get(url=url)
	quest_name = urllib.parse.unquote(url.replace("https://ff14.huijiwiki.com/wiki/",""))
	plot_quests = PlotQuest.objects.filter(name=quest_name)
	if len(plot_quests) > 0 and plot_quests[0].crawl_status==direction:
		print("Already crawled quest:{}".format(quest_name))
		return plot_quests[0]
	print("Crawling {}".format(quest_name))
	if("本页面目前没有内容" in r.text):
		print("Cannot find quest:{}".format(quest_name))
		return
	try:
		global to_crawl_list
		bs = BeautifulSoup(r.text,"html.parser")
		quick_fact = bs.find(class_="quest-quick-fact ff14-content-box hide-m")
		basic_info = quick_fact.find(class_="ff14-content-box-block--title",text="基本信息").parent
		info_list = basic_info.find_all("li")
		(q, q_created) = PlotQuest.objects.get_or_create(name=quest_name)
		for info in info_list:
			info_text = info.text
			if("版本：" in info_text):
				q.version = info_text.replace("版本：","")
			elif("所属地区：" in info_text):
				q.area = info_text.replace("所属地区：","")
			elif("主分类：" in info_text):
				q.category = info_text.replace("主分类：","")
			elif("子分类：" in info_text):
				q.sub_category = info_text.replace("子分类：","")
			elif("职业：" in info_text):
				q.job = info_text.replace("职业：","")
			elif("开始NPC：" in info_text):
				q.startnpc = info_text.replace("开始NPC：","")
			elif("结束NPC：" in info_text):
				q.endnpc = info_text.replace("结束NPC：","")
		q.html = r.text
		q.save()
		try:
			if(q.crawl_status==0):
				suf_quests = quick_fact.find(class_="ff14-content-box-block--title",text="后续任务").parent
				suf_list = suf_quests.find_all("a")
				for quest in suf_list:
					url = "https://ff14.huijiwiki.com"+quest.get("href")
					to_crawl_list.append((url,1))
		except AttributeError as e:
			print("No follow quest for {}".format(quest_name))
		q.crawl_status = 1
		q.save()
		try:
			if(q.crawl_status==1):
				pre_quests = quick_fact.find(class_="ff14-content-box-block--title",text="前置任务").parent
				pre_list = pre_quests.find_all("a")
				for quest in pre_list:
					url = "https://ff14.huijiwiki.com"+quest.get("href")
					to_crawl_list.append((url,2))
		except AttributeError as e:
			print("No follow quest for {}".format(quest_name))
		q.crawl_status = 2
		q.save()
		return q
	except Exception as e:
		print("Parse error: {}".format(e))
		traceback.print_exc() 
		raise e


def gen_relation(quest):
	try:
		q = quest
		# print("Generating relations of {}".format(q))
		bs = BeautifulSoup(q.html,"html.parser")
		quick_fact = bs.find(class_="quest-quick-fact ff14-content-box hide-m")
		basic_info = quick_fact.find(class_="ff14-content-box-block--title",text="基本信息").parent
		info_list = basic_info.find_all("li")
		try:
			suf_quests = quick_fact.find(class_="ff14-content-box-block--title",text="后续任务").parent
			suf_list = suf_quests.find_all("a")
			for quest in suf_list:
				url = "https://ff14.huijiwiki.com"+quest.get("href")
				suf_quest_name = urllib.parse.unquote(url.replace("https://ff14.huijiwiki.com/wiki/",""))
				suf_quest = PlotQuest.objects.filter(name=suf_quest_name)
				if(len(suf_quest)>0):
					suf_quest = suf_quest[0]
					q.suf_quests.add(suf_quest)
					# print("Add {} to the suf of {}".format(suf_quest, q))
		except AttributeError as e:
			# print("No follow quest for {}".format(q.name))
			pass
	except Exception as e:
		print("Parse error: {}".format(e))
		traceback.print_exc() 
		raise e

def search_all():
	quest_name = "任务:冒险者入门（枪术师）"
	url = "https://ff14.huijiwiki.com/wiki/{}".format(urllib.parse.quote(quest_name))
	to_crawl_list.append((url,1))
	while(len(to_crawl_list)>0):
		(url, direction) = to_crawl_list[0]
		try:
			search_quest(url, direction)
			to_crawl_list = to_crawl_list[1:]
		except Exception as e:
			to_crawl_list.append((url, direction))
			with codecs.open("to_crawl_list","w","utf8") as f:
				f.write(json.dumps(to_crawl_list))

def gen_all():
	quests = PlotQuest.objects.all()
	quests_len = len(quests)
	print("Generating quests relations")
	for i in range(quests_len):
		gen_relation(quests[i])
		progress(i/quests_len*100)
	print()

if __name__=="__main__":
	gen_all()
	