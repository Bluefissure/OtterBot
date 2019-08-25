import sys
import os
from django.db import DatabaseError, transaction
from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import re
import codecs
import copy
from bs4 import BeautifulSoup
import traceback
import base64
import time
from hashlib import sha1
import hmac

def get_image_from_CQ(CQ_text):
    if "url=" in CQ_text:
        tmp = CQ_text
        tmp = tmp[tmp.find("url=") : -1]
        tmp = tmp.replace("url=", "")
        img_url = tmp.replace("]", "")
        return img_url
    return None

@transaction.atomic
def QQCommand_share(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        WEIBO_TOKEN = global_config.get("WEIBO_TOKEN", None)
        WEIBO_SAFEURL = global_config.get("WEIBO_SAFEURL", None)
        TIMEFORMAT_MDHMS = global_config.get("TIMEFORMAT_MDHMS")
        ADMIN_ID = global_config.get("ADMIN_ID", "10000")
        action_list = []
        receive = kwargs["receive"]
        msg = "weibo share testing"
        para_segs = receive["message"].replace("/share","",1).replace("all","",1).split(" ")
        while "" in para_segs:
            para_segs.remove("")
        para_segs = list(map(lambda x:x.strip(), para_segs))
        (qq, _) = QQUser.objects.select_for_update().get_or_create(user_id = receive["user_id"])
        if len(para_segs) == 0 or para_segs[0] == "help":
            msg = "/share $msg：微博分享$msg"
        elif not (WEIBO_TOKEN and WEIBO_SAFEURL):
            msg = "管理员未配置微博分享功能，请联系开发者。"
        elif time.time() <= qq.ban_share_till:
            msg = "您需要等待至 {} 才能发送下一条微博~".format(
                    time.strftime(TIMEFORMAT_MDHMS,time.localtime(qq.ban_share_till))
                )
        else:
            content = " ".join(para_segs)
            img_url = get_image_from_CQ(content)
            url = "https://api.weibo.com/2/statuses/share.json"
            content = "✨投稿✨\n"+content
            if img_url:
                cqimg_pattern = r"\[CQ:image,file=([A-F0-9]+.(jpg|png|jpeg|webp|bmp|gif)),url=((\w+:\/\/)[-a-zA-Z0-9:@;?&=\/%\+\.\*!'\(\),\$_\{\}\^~\[\]`#|]+)\]"
                content = re.sub(cqimg_pattern, "", content)
                data = {
                    "access_token": WEIBO_TOKEN,
                    "status": "{}\nPowered by {}".format(content, WEIBO_SAFEURL),
                }
                r = requests.get(img_url, timeout=5)
                files = {'pic': r.content}
                r = requests.post(url=url, data=data, files=files, timeout=5)
            else:
                data = {
                    "access_token": WEIBO_TOKEN,
                    "status": "{}\nPowered by {}".format(content, WEIBO_SAFEURL),
                }
                r = requests.post(url=url, data=data, timeout=5)
            r_json = r.json()
            if r_json.get("error", None):
                msg = r_json.get("error", "default error")
            else:
                weibo_url = "https://m.weibo.cn/detail/{}".format(r_json.get("idstr"))
                msg = "微博发送成功，请访问：{}".format(weibo_url)
                qq.ban_share_till = time.time()+(3600 if qq.user_id != ADMIN_ID else 0)
                sent_weibo = json.loads(qq.sent_weibo)
                sent_weibo.append(r_json.get("id"))
                qq.sent_weibo = json.dumps(sent_weibo)
                qq.save(update_fields=['ban_share_till', 'sent_weibo'])
        # print("ruturning message:{}".format(msg))
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
