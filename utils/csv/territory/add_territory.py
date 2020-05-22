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

place_id2name = {}

def get_config():
    parser = argparse.ArgumentParser(description='Territory Auto-Sync Script')

    parser.add_argument('-d', '--download', action='store_true',
                        help='Download TerritoryType.csv and PlaceName.csv from ffxiv-datamining-cn')
    parser.add_argument('-u', '--update', action='store_true',
                        help='If so, update all territories.')
    # Parse args.
    args = parser.parse_args()
    # Namespace => Dictionary.
    kwargs = vars(args)
    return kwargs

def import_place_name_csv(csv_file, **kwargs):
    global place_id2name
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
                place_id = int(row[key_list.index("#")])
                place_name = row[key_list.index("Name")].strip()
                place_id2name[place_id] = place_name
                add_cnt += 1
        print("Imported {} PlaceName(s)".format(add_cnt))


def import_territory_csv(csv_file, **kwargs):
    global place_id2name
    with codecs.open(csv_file, "r", "utf8") as f:
        reader = csv.reader(f)
        key_list = key_type = []
        add_cnt = 0
        updated_cnt = 0
        updated = set()
        for row_id, row in enumerate(tqdm(reader)):
            if row_id==0:
                pass
            elif row_id==1:
                key_list = list(row)
            elif row_id==2:
                key_type = list(row)
            else:
                try:
                    rate_id = int(row[key_list.index("#")])
                    place_id = int(row[key_list.index("PlaceName")])
                    if not place_id:
                        continue
                    place_name = place_id2name[place_id]
                    if place_name in updated:
                        continue
                    (territory, created) = Territory.objects.get_or_create(name=place_name)
                    if created or kwargs.get("update", False):
                        wr_id = int(row[key_list.index("WeatherRate")])
                        map_id = int(row[key_list.index("Map")])
                        wr = WeatherRate.objects.get(id=wr_id)
                        jr = json.loads(wr.rate)
                        if place_name in ["雷克兰德","珂露西亚岛","安穆·艾兰","伊尔美格","拉凯提卡大森林","黑风海","水晶都","游末邦"] and jr[0][1] == 100:
                            continue
                        print("Adding Territory:{}".format(place_name))
                        territory.weather_rate = wr
                        territory.mapid = map_id
                        territory.save()
                        updated.add(place_name)
                        if kwargs.get("update", False):
                            updated_cnt += 1
                        else:
                            add_cnt += 1
                except IndexError as e:
                    print("Error at looking {} for PlaceName".format(place_id))
                    raise e
        if kwargs.get("update", False):
            print("Updated {} Territory(s)".format(updated_cnt))
        else:
            print("Imported {} Territory(s)".format(add_cnt))

if __name__ == "__main__":
    config = get_config()
    if config.get("download", False):
        if os.path.exists("TerritoryType.csv"):
            os.system("rm TerritoryType.csv")
        os.system(r"wget https://raw.githubusercontent.com/thewakingsands/ffxiv-datamining-cn/master/TerritoryType.csv")
        if os.path.exists("PlaceName.csv"):
            os.system("rm PlaceName.csv")
        os.system(r"wget https://raw.githubusercontent.com/thewakingsands/ffxiv-datamining-cn/master/PlaceName.csv")
    import_place_name_csv("PlaceName.csv", **config)
    import_territory_csv("TerritoryType.csv", **config)