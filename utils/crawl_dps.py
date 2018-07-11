#!/usr/bin/python3
import random
import sys
import os
import codecs
import urllib
import base64
sys.path.append('PATH_TO_FFXIVBOT')
os.environ['DJANGO_SETTINGS_MODULE'] ='FFXIVBOT.settings'
from FFXIVBOT import settings
import django
import string
import requests
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



def crawl_dps(boss,job):
	fflogs_url = 'https://www.fflogs.com/zone/statistics/table/%s/dps/%s/100/8/1/75/1000/7/0/Global/%s/All/normalized/single/0/-1/'%(boss.quest.quest_id,boss.boss_id,job.name)
	r = requests.get(url=fflogs_url)
	tot_days = 0
	percentage_list = [99,95,75,50,25,10]
	atk_res = {}
	for perc in percentage_list:
		day = 0
		re_str = 'series%s'%(perc)+r'.data.push\([+-]?(0|([1-9]\d*))(\.\d+)?\)'
		ptn = re.compile(re_str)
		find_res = ptn.findall(r.text)
		atk_res[str(perc)] = list(find_res)
		tot_days = len(find_res)
	print("\nboss:%s job:%s "%(boss,job))
	for day in range(0,tot_days):
		if(day < boss.parsed_days - 2):
			progress((day+1)*100/tot_days)
			continue
		tiles = DPSTile.objects.filter(boss=boss,job=job,day=day)
		if(len(tiles)>0):
			tl = tiles[0]
		else:
			tl = DPSTile(boss=boss,job=job,day=day)
		atk_json = json.loads(tl.attack)
		for perc in percentage_list:
			ss = atk_res[str(perc)][day][1]+atk_res[str(perc)][day][2]
			if(ss==""):
				ss = "0"
			atk = float(ss)
			atk_json.update({"%s"%(perc):atk})
		tl.attack = json.dumps(atk_json)
		tl.save()
		progress((day+1)*100/len(find_res))
	return tot_days


if __name__=="__main__":
	bs = Boss.objects.all()
	js = Job.objects.all()
	for b in bs:
		tot_days = 0
		for jb in js:
			tot_days = crawl_dps(b,jb)
		b.parsed_days = tot_days
		b.save()
