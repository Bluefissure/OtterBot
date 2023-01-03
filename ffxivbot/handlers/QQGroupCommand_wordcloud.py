from .QQEventHandler import QQEventHandler
from .QQUtils import *
from FFXIV import settings
from ffxivbot.models import *
import logging
import json
import traceback
import hashlib
import wordcloud
import base64
import redis
from collections import Counter
from PIL import Image as PILImage


def QQGroupCommand_wordcloud(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group_id = receive["group_id"]
        message = receive["message"].strip()

        if message == "/wordcloud":
            msg = """/wordcloud enable: 开启群词云记录
/wordcloud disable: 关闭群词云记录
/wordcloud clear: 清除群词云记录
/wordcloud generate: 生成群词云
"""
        elif user_info["role"] != "owner" and user_info["role"] != "admin":
            msg = "仅群主与管理员有权限设置、查看群词云"
        elif message.endswith("enable"):
            group.wordcloud = True
            group.save(update_fields=["wordcloud"])
            msg = "本群已开启词云记录功能"
        elif message.endswith("disable"):
            group.wordcloud = False
            group.save(update_fields=["wordcloud"])
            msg = "本群已关闭词云记录功能"
        elif message.endswith("clear"):
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            group_id_hash = hashlib.md5(
                ("{}|{}".format(group.group_id, settings.SECRET_KEY)).encode()
            ).hexdigest()
            group_mem = r.get(group_id_hash) or "{}"
            group_mem = json.loads(group_mem)
            group_mem["words"] = {}
            r.set(group_id_hash, json.dumps(group_mem))
            msg = "本群词云记录已清空"
        elif message.endswith("generate"):
            group_id_hash = hashlib.md5(
                ("{}|{}".format(group.group_id, settings.SECRET_KEY)).encode()
            ).hexdigest()
            r = redis.Redis(host="localhost", port=6379, decode_responses=True)
            group_mem = r.get(group_id_hash) or "{}"
            group_mem = json.loads(group_mem)
            word_cnt = Counter(group_mem.get("words", {}))
            if word_cnt:
                font_path = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "resources/font/msyh.ttc",
                )
                w = wordcloud.WordCloud(
                    width=1000,
                    height=700,
                    background_color="white",
                    font_path=font_path,
                )
                stopwords_file = os.path.join(
                    os.path.dirname(os.path.abspath(__file__)),
                    "resources/text/cn_stopwords.txt",
                )
                stopwords = set()
                with open(stopwords_file, "r", encoding="utf-8") as f:
                    for l in f.readlines():
                        stopwords.add(l.strip())
                words = {}
                for k, v in word_cnt.items():
                    if k not in stopwords:
                        words[k] = v
                w.generate_from_frequencies(words)
                img = w.to_image()
                output_buffer = io.BytesIO()
                img.save(output_buffer, format="JPEG")
                byte_data = output_buffer.getvalue()
                base64_str = base64.b64encode(byte_data).decode("utf-8")
                msg = "[CQ:image,file=base64://{}]\n".format(base64_str)
                del w
                del img
            else:
                msg = "没有已记录的群内聊天词频"
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return []
