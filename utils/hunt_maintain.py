#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import os
import time
import datetime
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'FFXIV.settings'
from FFXIV import settings
django.setup()
from ffxivbot.models import *


def hunt_maintain(keyword: str = '国', strtime: str = ''):
    if keyword == "国服" or keyword == '国':
        servers = Server.objects.all()
    elif keyword == "陆行鸟" or keyword == '鸟':
        servers = Server.objects.filter(areaId=1)
    elif keyword == "莫古力" or keyword == '猪':
        servers = Server.objects.filter(areaId=6)
    elif keyword == "猫小胖" or keyword == '猫':
        servers = Server.objects.filter(areaId=7)
    elif keyword == "豆豆柴" or keyword == '狗':
        servers = Server.objects.filter(areaId=8)
    else:
        servers = Server.objects.filter(name=keyword)

    if strtime != '':
        maintain_time = datetime.datetime.strptime(strtime + '+0800', '%Y%m%d_%H%M%S%z').timestamp()
    else:
        maintain_time = time.time()
    for s in servers:
        hunt_log = HuntLog(server=s, log_type="maintain", time=maintain_time)
        hunt_log.save()


if __name__ == "__main__":
    if len(sys.argv) > 1:
        hunt_maintain(*sys.argv[1:])
    else:
        hunt_maintain()
