from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
from bs4 import BeautifulSoup
import urllib
import logging
import time
import traceback


def revproxy(url):
    original_domain = "i.pximg.net"
    revproxy_domain = "pixiv.bluefissure.com"
    rev_url = url.replace(original_domain, revproxy_domain)
    return rev_url.replace("_webp", "")


def is_nsfw(illust):
    if int(illust["x_restrict"]) != 0:
        return True
    for item in illust["tags"]:
        if "R-18" in item["name"] or "R18" in item["name"]:
            return True
    return False


def search_image(img_url, qq=None):
    url_img_url = urllib.parse.quote(img_url)
    url = "https://saucenao.com/search.php?db=5&output_type=2&testmode=1&numres=16&url={}".format(
        url_img_url
    )
    r = requests.get(url=url, timeout=(5, 30))
    jres = json.loads(r.text)
    print("++++++++++++++++++\n{}".format(json.dumps(jres)))
    msg = "default msg"
    if "results" in jres.keys() and jres["results"]:
        result = jres["results"][0]
        if float(result["header"]["similarity"]) > 85:
            res_data = {
                "url": result["data"]["ext_urls"][0],
                "title": result["data"]["title"]
                if "title" in result["data"].keys()
                else "Result",
                "content": "Author:{}\nAuthorID:{}".format(
                    result["data"]["member_name"], result["data"]["member_id"]
                ),
                "image": result["header"]["thumbnail"],
            }
            msg = [{"type": "share", "data": res_data}]
        else:
            msg = "[CQ:at,qq={}] 找不到相似的图片".format(qq)
    return msg


def search_rank(mode, nsfw=False):
    the_day_before_yesterday_time = time.time() - 3600 * 24 * 2
    date = time.strftime("%Y-%m-%d", time.localtime(the_day_before_yesterday_time))
    url = "https://api.imjad.cn/pixiv/v2/?type=rank&mode={}&date={}".format(mode, date)
    # print("url:{}====================".format(url))
    r = requests.get(url=url, timeout=(5, 30))
    jres = json.loads(r.text)
    illusts = jres["illusts"]
    sfw_illusts = []
    if not nsfw:
        for item in illusts:
            if not is_nsfw(item):
                sfw_illusts.append(item)
        illusts = sfw_illusts
    if illusts:
        tot_num = len(illusts)
        illust = illusts[random.randint(0, tot_num - 1)]
        img_url = illust["image_urls"]["large"]
        msg = "[CQ:image,file={}]".format(revproxy(img_url))
        print(revproxy(img_url))
    else:
        msg = '未能找到排行榜"{}"'.format(mode)
    return msg


def search_word(word, nsfw=False):
    urlword = urllib.parse.quote(word)
    url = "https://api.imjad.cn/pixiv/v2/?type=search&word={}&page=1".format(urlword)
    r = requests.get(url=url, timeout=(5, 30))
    jres = json.loads(r.text)
    illusts = jres["illusts"]
    sfw_illusts = []
    if not nsfw:
        for item in illusts:
            if not is_nsfw(item):
                sfw_illusts.append(item)
        illusts = sfw_illusts
    if illusts:
        tot_num = len(illusts)
        illust = illusts[random.randint(0, tot_num - 1)]
        img_url = illust["image_urls"]["large"]
        msg = "[CQ:image,file={}]".format(revproxy(img_url))
        # print("msg:{}====================".format(msg))
    else:
        msg = '未能找到搜索关键词"{}"'.format(word)
    return msg


def search_ID(ID):
    url = "https://api.imjad.cn/pixiv/v2/?type=illust&id={}".format(ID)
    r = requests.get(url=url, timeout=(5, 30))
    jres = json.loads(r.text)
    if "error" in jres.keys():
        msg = jres["error"]["user_message"] or jres["error"]["message"]
    else:
        illust = jres["illust"]
        img_url = illust["image_urls"]["large"]
        msg = "[CQ:image,file={}]".format(revproxy(img_url))
    return msg


def search_gif_ID(ID):
    url = "http://ugoira.dataprocessingclub.org/convert?url=https%3A%2F%2Fwww.pixiv.net%2Fmember_illust.php%3Fmode%3Dmedium%26illust_id%3D{}&format=gif".format(
        ID
    )
    r = requests.get(url=url, timeout=(5, 60))
    jres = json.loads(r.text)
    if "url" in jres.keys():
        sz_M = int(jres["size_bytes"]) / 1024 / 1024
        img_url = jres["url"]
        if sz_M > 2:
            msg = "图片过大，请手动访问：{}".format(img_url)
        else:
            msg = "[CQ:image,file={}]".format(img_url)
    return msg


def QQCommand_pixiv(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        bot = kwargs["bot"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        FF14WIKI_API_URL = global_config["FF14WIKI_API_URL"]
        FF14WIKI_BASE_URL = global_config["FF14WIKI_BASE_URL"]
        receive = kwargs["receive"]
        user = QQUser.objects.get(user_id=receive["user_id"])

        if time.time() < user.last_api_time + 15:
            msg = "[CQ:at,qq={}] 技能冷却中".format(user)
        else:
            update_api_cooldown = False
            message_content = receive["message"].replace("/pixiv", "", 1).strip()
            msg = "default msg"
            if message_content.find("help") == 0 or message_content == "":
                msg = (
                    "/pixiv $keyword : 搜索关键词$keyword并随机返回\n"
                    + "/pixiv $ID : 返回编号为ID的图(NSFW注意)\n"
                    + "/pixiv gif $ID : 返回编号为ID的动图(耗时超久，请酌情调用)\n"
                    + "/pixiv $img : 在P站以图搜图(用法参考/anime功能)\n"
                    + "/pixiv rank $mode : 随机返回一个排行榜的图片(可用mode: day, week, month等)\n"
                    + "PS: 利用此功能发送NSFW图片的行为请等同于调用命令者发送\n"
                    + "Powered by https://api.imjad.cn, https://saucenao.com and http://ugoira.dataprocessingclub.org/"
                )
            elif message_content.find("rank") == 0:
                mode = message_content.replace("rank", "", 1).strip()
                if mode == "":
                    mode = "week"
                msg = search_rank(mode, receive["message_type"] != "group")
                update_api_cooldown = True
            elif message_content.find("gif") == 0:
                ID = message_content.replace("gif", "", 1).strip()
                msg = search_gif_ID(ID)
                update_api_cooldown = True
            elif str.isdecimal(message_content):
                ID = int(message_content)
                msg = search_ID(ID)
                update_api_cooldown = True
            elif "CQ" in message_content and "url=" in message_content:
                # print("matching image:{}".format(message_content))
                tmp = message_content
                tmp = tmp[tmp.find("url=") : -1]
                tmp = tmp.replace("url=", "")
                img_url = tmp.replace("]", "")
                msg = search_image(img_url, receive["user_id"])
                update_api_cooldown = True
            else:
                word = message_content
                msg = search_word(word, receive["message_type"] != "group")
                update_api_cooldown = True
            if update_api_cooldown:
                user.last_api_time = time.time()
                user.save(update_fields=["last_api_time"])
        if isinstance(msg, str):
            msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        logging.error(e)
        traceback.print_exc()
    return action_list
