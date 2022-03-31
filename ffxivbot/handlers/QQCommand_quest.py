from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
from difflib import SequenceMatcher
import logging
import json
import random
import traceback
import urllib


def bfs_quest(quest):
    from queue import Queue

    Q = Queue()
    Q.put(quest)
    now_main_scenario = "Endwalker主线任务(6.0)"
    # back search
    back_cnt = 0
    visited = set()
    while not Q.empty() and back_cnt < 10000:
        q = Q.get(False)
        if q.id in visited:
            continue
        back_cnt += 1
        visited.add(q.id)
        if q.endpoint:
            break
        for pre_q in q.pre_quests.all():
            if pre_q.is_main_scenario():
                Q.put(pre_q)
    # forward search
    forward_cnt = 0
    visited.clear()
    Q.put(quest)
    while not Q.empty() and forward_cnt < 10000:
        q = Q.get(False)
        if q.id in visited:
            continue
        forward_cnt += 1
        visited.add(q.id)
        if q.endpoint:
            now_main_scenario = q.endpoint_desc
            break
        for pre_q in q.suf_quests.all():
            if pre_q.is_main_scenario():
                Q.put(pre_q)
    back_cnt -= 1
    forward_cnt -= 1
    return {
        "back_cnt": back_cnt,
        "now_main_scenario": now_main_scenario,
        "forward_cnt": forward_cnt,
    }

def get_banner(quest_id):
    API_URL = "https://cafemaker.wakingsands.com"
    INTL_API_URL = "https://xivapi.com"
    api_base = API_URL
    banner_url = ""
    r = requests.get("{}/quest/{}".format(api_base, quest_id), timeout=5)
    if r.status_code != 200:
        api_base = INTL_API_URL
        r = requests.get("{}/quest/{}".format(api_base, quest_id), timeout=5)
        if r.status_code != 200:
            return ""
    quest_data = r.json()
    if "Banner" in quest_data and quest_data["Banner"] != "":
        banner_url = "{}{}".format(api_base, quest_data["Banner"])
    return banner_url


def search_quest(quest_name):
    msg = ""
    quests = PlotQuest.objects.filter(name__icontains=quest_name)
    if not quests.exists():
        quests = PlotQuest.objects.filter(language_names__icontains=quest_name)
    if not quests.exists():
        quests = []
        all_quests = PlotQuest.objects.all()
        for q in all_quests:
            jname = json.loads(q.language_names)
            for k, v in jname.items():
                if quest_name in v:
                    quests.append(q)
    else:
        quests = list(quests)
        quests.reverse()
    if not quests:
        msg = '找不到任务"{}"，请检查后查询'.format(quest_name)
    else:
        quest = max(quests, key=lambda x: SequenceMatcher(None, str(x), quest_name).ratio())
        if quest.is_main_scenario():
            quest_img_url = (
                "https://huiji-public.huijistatic.com/ff14/uploads/4/4a/061432.png"
            )
            bfs_res = bfs_quest(quest)
            # fmt: off
            percent = (bfs_res["back_cnt"]+1)*100/(bfs_res["back_cnt"]+1+bfs_res["forward_cnt"])
            # fmt: on
            content = "{}进度已达到{:.2f}%，剩余{}个任务".format(
                bfs_res["now_main_scenario"], percent, bfs_res["forward_cnt"]
            )
        elif quest.is_special():
            quest_img_url = (
                "https://huiji-public.huijistatic.com/ff14/uploads/4/4c/061439.png"
            )
            content = "特殊支线任务"
        else:
            quest_img_url = (
                "https://huiji-public.huijistatic.com/ff14/uploads/6/61/061431.png"
            )
            content = "支线任务"
        lname = json.loads(quest.language_names)
        url = "https://ff14.huijiwiki.com/wiki/{}".format(
            urllib.parse.quote("任务:" + str(quest))
        ) if "cn" in lname else ("https://www.garlandtools.org/db/#quest/{}".format(quest.id))
        banner_url = ""
        try:
            banner_url = get_banner(quest.id)
        except Exception as e:
            logging.warning(e)
        msg = [
            {
                "type": "share",
                "data": {
                    "url": url,
                    "title": "{}".format(quest.name),
                    "content": content,
                    "image": quest_img_url,
                    "banner": banner_url,
                },
            }
        ]
    return msg


def QQCommand_quest(*args, **kwargs):
    action_list = []
    try:
        receive = kwargs["receive"]
        receive_message = receive["message"]
        quest_name = receive_message.replace("/quest", "").strip()
        msg = search_quest(quest_name)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc()
    return action_list
