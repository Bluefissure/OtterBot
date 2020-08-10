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

# import pymysql
import time
from time import strftime, localtime
from ffxivbot.models import *
from ffxivbot.handlers.QQUtils import *
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from hashlib import md5
import math
import requests
import base64
import random
import sys
import traceback
import codecs
import html
import hmac
from bs4 import BeautifulSoup
import urllib
from websocket import create_connection


def webapi(req):
    res_dict = {"response": "error", "msg": "Request not handled", "rcode": "102"}
    try:
        req_json = json.loads(req.body)
        req_data = req_json["data"]
        request_type = req_json["request"]
        if request_type == "weather":
            territory_name = req_data["territory"]
            territory = None
            try:
                territory = Territory.objects.get(name=territory_name)
            except Territory.DoesNotExist:
                for temp in Territory.objects.all():
                    for temp_name in json.loads(temp.nickname):
                        if temp_name in territory_name or territory_name in temp_name:
                            territory = temp
                            break
                    if territory:
                        break
            if not territory:
                res_dict = {
                    "response": "error",
                    "msg": "Territory {} not found".format(territory_name),
                    "rcode": "1001",
                }
            else:
                weather_name = (
                    None if "weather" not in req_data.keys() else req_data["weather"]
                )
                length = 10 if "length" not in req_data.keys() else req_data["length"]
                length = min(length, 100)
                length = max(length, -100)
                TIMEFORMAT_MDHMS = "%Y-%m-%d %H:%M:%S"
                if weather_name:
                    try:
                        weathers = Weather.objects.filter(name=weather_name)
                        times = getSpecificWeatherTimes(
                            territory, weathers, length, TIMEFORMAT_MDHMS
                        )
                        res_dict = {
                            "response": "success",
                            "msg": "",
                            "rcode": "0",
                            "data": times,
                        }
                    except Weather.DoesNotExist:
                        res_dict = {
                            "response": "error",
                            "msg": "Weather {} not found".format(weather_name),
                            "rcode": "1002",
                        }
                else:
                    times = getFollowingWeathers(
                        territory, length, TIMEFORMAT_MDHMS, unixSeconds=time.time()
                    )
                    res_dict = {
                        "response": "success",
                        "msg": "",
                        "rcode": "0",
                        "data": times,
                    }

        elif request_type == "dps":
            boss_name = req_data["boss"]
            boss_obj = None
            CN_source = False
            boss_list = Boss.objects.all()
            for boss in boss_list:
                try:
                    boss_nicknames = json.loads(boss.nickname)["nickname"]
                except KeyError:
                    boss_nicknames = []
                boss_nicknames.append(boss.name)
                boss_nicknames.append(boss.cn_name)
                boss_nicknames.sort(key=len, reverse=True)
                for item in boss_nicknames:
                    if boss_name.find(item) == 0:
                        boss_obj = boss
                        break
                if boss_obj:
                    break
            if not boss_obj:
                res_dict = {
                    "response": "error",
                    "msg": "Boss {} not found",
                    "rcode": "1011",
                }
            else:
                job_name = req_data["job"]
                job_list = Job.objects.all()
                job_obj = None
                for job in job_list:
                    try:
                        job_nicknames = json.loads(job.nickname)["nickname"]
                    except KeyError:
                        job_nicknames = []
                    job_nicknames.append(job.name)
                    job_nicknames.append(job.cn_name)
                    job_nicknames.sort(key=len, reverse=True)
                    for item in job_nicknames:
                        if job_name.find(item) == 0:
                            job_obj = job
                            break
                    if job_obj:
                        break
                if not job_obj:
                    res_dict = {
                        "response": "error",
                        "msg": "Job {} not found",
                        "rcode": "1012",
                    }
                else:
                    CN = req_data["CN"] if "CN" in req_data.keys() else False
                    day = (
                        req_data["day"]
                        if "day" in req_data.keys()
                        else math.ceil(
                            (int(time.time()) - boss_obj.cn_add_time) / (24 * 3600)
                        )
                    )
                    atk_res = crawl_dps(
                        boss=boss_obj, job=job_obj, day=day, CN_source=CN
                    )
                    if isinstance(atk_res, str):
                        res_msg = atk_res.replace("Error:", "", 1)
                        res_dict = {
                            "response": "error",
                            "msg": "DPS parsing error: {}".format(res_msg),
                            "rcode": "1013",
                        }
                    else:
                        res_dict = {
                            "response": "success",
                            "msg": "",
                            "rcode": "0",
                            "data": {
                                "day": day,
                                "source": ("CN" if CN else "Intl"),
                                "dps": atk_res,
                            },
                        }

        elif request_type == "search":  # 102X
            name = req_data["name"]
            search_res = search_item(
                name,
                "https://ff14.huijiwiki.com",
                "https://cdn.huijiwiki.com/ff14/api.php",
                url_quote=False,
            )
            res_dict = {
                "response": "success",
                "msg": "",
                "rcode": "0",
                "data": search_res,
            }
        elif request_type == "raid":  # 103X
            wol_name = req_data["name"]
            server_name = req_data["server"]
            server = None
            servers = Server.objects.all()
            for s in servers:
                if server_name in str(s.name) or server_name in str(s.alter_names):
                    server = s
            if not server:
                res_dict = {
                    "response": "error",
                    "msg": "Server {} not found".format(server_name),
                    "rcode": "1031",
                }
            else:
                raid_data = {}
                data = {
                    "method": "queryhreodata",
                    "name": wol_name,
                    "areaId": server.areaId,
                    "groupId": server.groupId,
                }
                r = requests.post(
                    url="http://act.ff.sdo.com/20180525HeroList/Server/HeroList171213.ashx",
                    data=data,
                )
                res = json.loads(r.text)
                raid_data.update({"sigma": res})
                r = requests.post(
                    url="http://act.ff.sdo.com/20171213HeroList/Server/HeroList171213.ashx",
                    data=data,
                )
                res = json.loads(r.text)
                raid_data.update({"delta": res})
                res_dict = {
                    "response": "success",
                    "msg": "",
                    "rcode": "0",
                    "data": {
                        "name": wol_name,
                        "server": server_name,
                        "raid": raid_data,
                    },
                }

    except json.decoder.JSONDecodeError:
        res_dict = {"response": "error", "msg": "JSON decode error", "rcode": "103"}
    except KeyError:
        res_dict = {"response": "error", "msg": "KeyError", "rcode": "104"}
    except TypeError:
        res_dict = {"response": "error", "msg": "Parameter type error", "rcode": "105"}
    except Exception as e:
        res_dict = {
            "response": "error",
            "msg": "Unhandled Exception: {}".format(e),
            "rcode": "-1",
        }
    return res_dict


def github_webhook(req):
    req_json = json.loads(req.body)
    event_type = req.META.get("HTTP_X_GITHUB_EVENT")
    msg = None
    if not event_type:
        pass
        # return HttpResponse("Can't get github event type.", status=500)
    elif event_type == "ping":
        msg = req_json.get("zen", "Hello from github")
    elif event_type == "push":
        pusher = req_json.get("pusher")
        repo = req_json.get("repository")
        msg = "New push to {}:\n".format(repo.get("full_name"))
        msg += "Pusher: {}\n".format(pusher.get("name") or pusher.get("username"))
        msg += "Ref: {}\n".format(req_json.get("ref"))
        msg += "Commits:\n"
        for commit in req_json.get("commits"):
            msg += "  {}: {}\n".format(commit["id"][:7], commit["message"])
        msg += "Check at {}".format(req_json.get("compare") or req_json.get("compare_url"))
    elif event_type == "pull_request":
        action = req_json.get("action")
        number = req_json.get("number")
        pr = req_json.get("pull_request")
        repo = req_json.get("repository")
        pusher = pr.get("user").get("login")
        if action == "opened":
            msg = "{} opened a new pull request to {}:\n".format(
                pusher, repo.get("full_name")
            )
            msg += "#{}:{}\n".format(number, pr.get("title"))
        else:
            msg += "{} {} PR#{}:{}, state changed to {}.\n".format(
                pusher, action, number, pr.get("title"), pr.get("state")
            )
        msg += "Check at {}\n".format(pr.get("html_url"))
    elif event_type == "star":
        action = req_json.get("action")
        sender = req_json.get("sender")
        repo = req_json.get("repository")
        if action == "created":
            msg = "{} stared {}".format(sender.get("login"), repo.get("full_name"))
        elif action == "deleted":
            msg = "{} canceled star of {}".format(
                sender.get("login"), repo.get("full_name")
            )
    elif event_type == "issues":
        action = req_json.get("action")
        issue = req_json.get("issue")
        number = issue.get("number")
        repo = req_json.get("repository")
        pusher = issue.get("user").get("login")
        if action == "opened":
            msg = "{} opened a new issue to {}:\n".format(pusher, repo.get("full_name"))
            msg += "#{}:{}\n".format(number, issue.get("title"))
        else:
            msg += "{} {} issue#{}:{}, state changed to {}.\n".format(
                pusher, action, number, issue.get("title"), issue.get("state")
            )
        msg += "Check at {}\n".format(issue.get("html_url"))
    elif event_type == "fork":
        forkee = req_json.get("forkee")
        repo = req_json.get("repository")
        msg = "{} forked {} to {}".format(
            forkee.get("owner").get("login"),
            repo.get("full_name"),
            forkee.get("full_name"),
        )
    elif event_type == "gollum":
        pages = req_json.get("pages")
        sender = req_json.get("sender")
        repo = req_json.get("repository")
        msg = "{} updated wiki pages of {}:\n".format(
            sender.get("login"), repo.get("full_name")
        )
        for page in pages:
            msg += "{}:{}\n".format(page.get("page_name"), page.get("html_url"))
        msg = msg.strip()
    else:
        msg = 'Github event "{}" is not implemented.'.format(event_type)
    return msg
