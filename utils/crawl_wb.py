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
			t.save()
			print("crawled {} of {}".format(t.itemid, t.owner))
	else:
		print("Error at crawling weibo:{}".format(jdata["ok"]))
		pass
	return 

if __name__=="__main__":
	wbus = WeiboUser.objects.all()
	for wbu in wbus:
		print("Begin crawling {}".format(wbu.name))
		try:
			crawl_wb(wbu)
		except Exception as e:
			print(e)
		time.sleep(1)
		print("Crawl {} finish".format(wbu.name))