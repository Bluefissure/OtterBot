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
    parser = argparse.ArgumentParser(description='Weather Auto-Sync Script')

    parser.add_argument('-d', '--download', action='store_true',
                        help='Download Territory.csv from ffxiv-datamining-cn')
    # Parse args.
    args = parser.parse_args()
    # Namespace => Dictionary.
    kwargs = vars(args)
    return kwargs

def import_weather_from_csv(csv_file, **kwargs):
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
                weather_id = int(row[key_list.index("#")])
                weather_name = row[key_list.index("Name")].strip()
                if not weather_name:
                    continue
                (weather, created) = Weather.objects.get_or_create(id=weather_id)
                if created:
                    weather.name = weather_name
                    print("Adding Weather {}".format(weather_name))
                    weather.save()
                    add_cnt += 1
        print("Imported {} WeatherRates".format(add_cnt))


def import_weatherrate_from_csv(csv_file, **kwargs):
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
                rate_id = int(row[key_list.index("#")])
                (rate, created) = WeatherRate.objects.get_or_create(id=rate_id)
                if created:
                    rate_list = []
                    for i in range(1, len(row), 2):
                        rate_list.append([int(row[i]), int(row[i + 1])])
                    print("Adding WeatherRate#{}:{}".format(rate_id, rate_list))
                    rate.rate = json.dumps(rate_list)
                    rate.save()
                    add_cnt += 1
        print("Imported {} WeatherRates".format(add_cnt))

if __name__ == "__main__":
    config = get_config()
    if config.get("download", False):
        if os.path.exists("WeatherRate.csv"):
            os.system("rm WeatherRate.csv")
        os.system(r"wget https://github.com/thewakingsands/ffxiv-datamining-cn/raw/master/WeatherRate.csv")
        if os.path.exists("Weather.csv"):
            os.system("rm Weather.csv")
        os.system(r"wget https://github.com/thewakingsands/ffxiv-datamining-cn/raw/master/Weather.csv")
    import_weather_from_csv("Weather.csv", **config)
    import_weatherrate_from_csv("WeatherRate.csv", **config)