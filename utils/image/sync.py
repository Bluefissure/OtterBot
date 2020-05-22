#!/usr/bin/env python3
import sys
import os
import django
sys.path.append((os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
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
import traceback
from tqdm import tqdm


def get_config():
    parser = argparse.ArgumentParser(description='Image Auto-Sync Script')

    parser.add_argument('-l', '--load', action='store_true',
                        help='Load images from the resource file')
    parser.add_argument('-u', '--user',
                        help='The uploader user_id of imported images')
    parser.add_argument('-s', '--save', action='store_true',
                        help='Save images to the resource file')
    parser.add_argument('-f', '--file', default="images.txt",
                        help='The resource file')
    # Parse args.
    args = parser.parse_args()
    # Namespace => Dictionary.
    kwargs = vars(args)
    return kwargs

def load_images(**config):
    user_id = config.get("user", None)
    users = QQUser.objects.filter(user_id=user_id)
    if not users:
        print("You must provide a user to manage the images")
        exit(1)
    user = users[0]
    file = config.get("file", "images.txt")
    ok_cnt = 0
    with codecs.open(file, "r", "utf8") as f:
        lines = f.readlines()
        for line in tqdm(lines):
            j = json.loads(line)
            try:
                img = Image(
                    domain=j["domain"],
                    key=j["key"],
                    name=j["name"],
                    path=j["path"],
                    img_hash="null",
                    timestamp=int(time.time()),
                    add_by=user,
                )
                img.save()
                ok_cnt += 1
            except Exception as e:
                traceback.print_exc()
        print("Loaded {} images, {} failed.".format(ok_cnt, len(lines)-ok_cnt))

def save_images(**config):
    keywords = ["色", "hso", "猫", "cat", "獭", "笑话", "骑", "DK", "武", "枪刃", "战士",
        "占星", "白魔", "学者", "赤魔", "召唤", "黑魔", "青魔", "诗人", "吟游", "舞者", "机工",
        "忍者", "武士", "武僧", "龙骑", "抛竿"]
    ok_cnt = 0
    file = config.get("file", "images.txt")
    with codecs.open(file, "w", "utf8") as f:
        for img in Image.objects.all():
            if any([x in img.key for x in keywords]):
                d = {
                    "domain": img.domain,
                    "key": img.key,
                    "name": img.name,
                    "path": img.path,
                }
                line = json.dumps(d)
                f.write(line)
                f.write("\n")
                ok_cnt += 1
    print("Dumped {} images to {}".format(ok_cnt, file))

if __name__ == "__main__":
    config = get_config()
    if config.get("load", False):
        load_images(**config)
    elif config.get("save", False):
        save_images(**config)
    else:
        print("Add '--help' in arguments for more information.")
