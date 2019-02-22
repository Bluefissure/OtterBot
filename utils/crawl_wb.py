#!/usr/bin/env python3
import random
import sys
import os
import codecs
import urllib
import base64
sys.path.append('/root/FFXIVBOT/')
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIV.settings'
from FFXIV import settings
import django
import string
import requests
import time
import json
import re
from django.db import connection, connections
django.setup()
from ffxivbot.models import *
from channels.layers import get_channel_layer 
from asgiref.sync import async_to_sync
from ffxivbot.handlers.QQUtils import *

def progress(percent,width=50):
    if percent >= 100:
        percent=100
    show_str=('[%%-%ds]' %width) %(int(width * percent/100)*"#")
    print('\r%s %d%%' %(show_str,percent),end='')


def crawl_wb(weibouser):
	uid = weibouser.uid
	containerid = weibouser.containerid
	url = r'https://m.weibo.cn/api/container/getIndex?type=uid&value={}&containerid={}'.format(uid,containerid)
	s = requests.post(url=url)
	jdata = json.loads(s.text)
	if(jdata["ok"]==1):
		for tile in jdata["data"]["cards"]:
			if(len(WeiboTile.objects.filter(itemid=tile["itemid"]))>0):
				# print("crawled {} of {} before, pass".format(tile["itemid"], tile["itemid"]))
				continue
			t = WeiboTile(itemid=tile["itemid"])
			t.owner = weibouser
			t.content = json.dumps(tile)
			t.crawled_time = int(time.time())
			if(tile["itemid"]==""):
				print("pass {} of {} cuz empty itemid".format(t.itemid, t.owner))
				continue
			channel_layer = get_channel_layer()
			groups = weibouser.subscribed_by.filter(subscription_trigger_time=-1)
			# print("ready to push groups:{}".format(groups))
			bots = QQBot.objects.all()
			t.save()
			try:
				for bot in bots:
					group_id_list = [item["group_id"] for item in json.loads(bot.group_list)]
					#print("group_id_list:{}".format(group_id_list))
					for group in groups:
						if int(group.group_id) in group_id_list:
							msg = get_weibotile_share(t, mode="text")
							# print("Pushing {} to group: {}".format(t, group))
							# print("msg: {}".format(msg))
							t.pushed_group.add(group)
							jdata = {
								"action":"send_group_msg",
								"params":{"group_id":int(group.group_id),"message":msg},
								"echo":"",
							}
							async_to_sync(channel_layer.send)(bot.api_channel_name, {"type": "send.event","text": json.dumps(jdata),})
				t.save()
			except Exception as e:
				print("Error at pushing crawled weibo: {}".format(e))

			print("crawled {} of {}".format(t.itemid, t.owner))
	else:
		print("Error at crawling weibo:{}".format(jdata["ok"]))
		pass
	return

def crawl():
	wbus = WeiboUser.objects.all()
	for wbu in wbus:
		print("Begin crawling {}".format(wbu.name))
		try:
			crawl_wb(wbu)
		except Exception as e:
			print(e)
		time.sleep(1)
		print("Crawl {} finish".format(wbu.name))



if __name__=="__main__":
	crawl()
