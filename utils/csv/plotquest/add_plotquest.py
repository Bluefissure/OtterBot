#!/usr/bin/env python3
import sys
import os
import django

sys.path.append(
    os.path.dirname(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    )
)
os.environ["DJANGO_SETTINGS_MODULE"] = "FFXIV.settings"
from FFXIV import settings

django.setup()
from ffxivbot.models import *
import re
import json
import time
import requests
import string
import random
import codecs
import urllib
import base64
import logging
import csv
import argparse
import traceback
from tqdm import tqdm


def get_config():
    parser = argparse.ArgumentParser(description="Quest Auto-Sync Script")

    parser.add_argument(
        "-d",
        "--download",
        action="store_true",
        help="Download Quest.csv from ffxiv-datamining-cn",
    )
    parser.add_argument(
        "-l", "--language", choices=["cn", "en", "jp"], help="Quest Language"
    )
    # Parse args.
    args = parser.parse_args()
    # Namespace => Dictionary.
    kwargs = vars(args)
    return kwargs


end_point_map = {
    # 海之都与沙之都
    # 66043: "格里达尼亚起始任务",
    # 海之都与森之都
    # 66064: "乌尔达哈起始任务",
    # 森之都与沙之都
    # 66082: "利姆萨·罗敏萨起始任务",
    # 超越幻想，究极神兵
    70058: "重生之境主线任务(2.0)",
    # 希望的灯火
    65964: "第七星历主线任务(2.x)",
    # 苍穹之禁城
    67205: "苍穹之禁城主线任务(3.0)",
    # 绝命怒嚎
    67783: "龙诗战争终章主线任务(3.1-3.3)",
    # 命运的止境
    67895: "龙诗战争尾声主线任务(3.4-3.56)",
    # 红莲之狂潮
    68089: "红莲之狂潮主线任务(4.0)",
    # 英雄挽歌
    68721: "解放战争战后主线任务(4.x)",
    # 暗影之逆焰
    69190: "暗影之逆焰主线任务(5.0)",
    # 水晶的残光
    69318: "拂晓回归主线任务(5.1-5.3)",
    # 死斗至黎明
    69602: "末日序曲主线任务(5.4-5.55)",
    # 晓月之终途
    70000: "晓月之终途主线任务(6.0)",
    # 弗栗多的决断
    70071: "崭新的冒险主线任务(6.1)"
}


def import_plotquest_from_csv(csv_file, **kwargs):
    language = kwargs.get("language", "cn")
    deprecated_quests = []
    with codecs.open(csv_file, "r", "utf8") as f:
        reader = csv.reader(f)
        key_list = key_type = []
        add_cnt = 0
        for row_id, row in enumerate(tqdm(reader)):
            if row_id == 0:
                pass
            elif row_id == 1:
                key_list = list(row)
            elif row_id == 2:
                key_type = list(row)
            else:
                quest_id = int(row[key_list.index("#")])
                quest_name = row[key_list.index("Name")].strip()
                quest_type_str = row[key_list.index("EventIconType")].replace('EventIconType#', '')
                quest_type = int(quest_type_str or 0)
                #Read bool for if is deprecated
                is_deprecated = row[key_list.index("SortKey") + 1] == "True"
                if not quest_name:
                    continue
                if is_deprecated:
                    # print(f"Deleting deprecated quest {quest_name} (id {quest_id})")
                    # (quest, created) = PlotQuest.objects.get_or_create(id=quest_id)
                    deprecated_quests.append(quest_id)
                    # PlotQuest.delete(quest)
                    # continue

                (quest, created) = PlotQuest.objects.get_or_create(id=quest_id)
                new_name = (
                    quest_name.replace("\ue0be", "").replace("\ue0bf", "").strip()
                )

                if language == "cn" or created:
                    quest.name = new_name
                quest.quest_type = quest_type
                quest.is_deprecated = is_deprecated
                lname = json.loads(quest.language_names)
                lname.update({language: new_name})
                quest.language_names = json.dumps(lname)

                #Update the endpoint
                if end_point_map.get(quest_id) is not None:
                    quest.endpoint_desc = end_point_map.get(quest_id)
                    quest.endpoint = True
                else:
                    quest.endpoint = False
                    quest.endpoint_desc = ""
                # pre_quests_cnt = int(row[key_list.index("PreviousQuestJoin")])
                quest.save()
                
                #Clear pre_quests before
                quest.pre_quests.clear()
                for i in range(3):
                    pre_key = "PreviousQuest[{}]".format(i)
                    try:
                        pre_quest_id = int(row[key_list.index(pre_key)])
                        if pre_quest_id <= 0:
                            continue
                        # assert pre_quest_id > 0
                    except (ValueError, AssertionError):
                        pass
                    else:
                        try:
                            pre_quest = PlotQuest.objects.get(id=pre_quest_id)
                        except PlotQuest.DoesNotExist:
                            print(f"Quest id:{pre_quest_id} not found, please import again")
                        else:
                            quest.pre_quests.add(pre_quest)

                quest.save()
                add_cnt += 1
        print("Imported {} quests".format(add_cnt))
        print("{} quests are deprecated".format(len(deprecated_quests)))


if __name__ == "__main__":
    config = get_config()
    if config.get("download", False):
        if os.path.exists("Quest.csv"):
            os.system("rm Quest.csv")
        os.system(
            r"wget https://github.com/thewakingsands/ffxiv-datamining-cn/raw/master/Quest.csv"
        )
    import_plotquest_from_csv("Quest.csv", **config)
