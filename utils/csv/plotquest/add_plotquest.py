#!/usr/bin/env python3
import sys
import os
import django
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'FFXIV.settings'
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
from tqdm import tqdm


def get_config():
    parser = argparse.ArgumentParser(description='Quest Auto-Sync Script')

    parser.add_argument('-d', '--download', action='store_true',
                        help='Download Quest.csv from ffxiv-datamining-cn')
    # Parse args.
    args = parser.parse_args()
    # Namespace => Dictionary.
    kwargs = vars(args)
    return kwargs


def import_plotquest_from_csv(csv_file):
    with codecs.open(csv_file, "r", "utf8") as f:
        reader = csv.reader(f)
        key_list = key_type = []
        add_cnt = 0
        for row_id, row in enumerate(tqdm(reader)):
            if row_id==0:
                pass
            elif row_id==1:
                key_list = list(row)
            elif row_id==2:
                key_type = list(row)
            else:
                quest_id = int(row[key_list.index("#")])
                quest_name = row[key_list.index("Name")].strip()
                quest_type = row[key_list.index("EventIconType")]
                if not quest_name:
                    continue
                (quest, created) = PlotQuest.objects.get_or_create(id=quest_id)
                quest.name = quest_name.replace("\ue0be","").replace("\ue0bf","").strip()
                quest.quest_type = quest_type
                pre_quests_cnt = int(row[key_list.index("PreviousQuestJoin")])
                quest.save()
                # if quest.id==66413:
                #     print("name:{}\nquest_type:{}\npre_quests_cnt:{}".format(quest.name, quest.quest_type, pre_quests_cnt))
                for i in range(pre_quests_cnt):
                    pre_key = 'PreviousQuest[{}]'.format(i)
                    try:
                        pre_quest_id = int(row[key_list.index(pre_key)])
                        # if quest.id==66413:
                        #     print("pre_quest_id:{}".format(pre_quest_id))
                        assert pre_quest_id > 0
                    except (ValueError, AssertionError):
                        pass
                    else:
                        try:
                            pre_quest = PlotQuest.objects.get(id=pre_quest_id)
                            # if quest.id==66413:
                            #     print("pre_quest:{}".format(pre_quest))
                        except PlotQuest.DoesNotExist:
                            print("Quest id:{} not found, please import again".format(pre_quest_id))
                        else:
                            quest.pre_quests.add(pre_quest)
                quest.save()
                add_cnt += 1
                # print(quest_id)
                # break
        print("Imported {} quests".format(add_cnt))

if __name__ == "__main__":
    config = get_config()
    if config.get("download", False):
        if os.path.exists("Quest.csv"):
            os.system("rm Quest.csv")
        os.system(r"wget https://github.com/thewakingsands/ffxiv-datamining-cn/raw/master/Quest.csv")
    import_plotquest_from_csv("Quest.csv")