from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
from bs4 import BeautifulSoup


def QQCommand_gif(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        SORRY_BASE_URL = global_config["SORRY_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        sorrygifs = SorryGIF.objects.all()
        sorry_dict = {}
        sorry_name = {}
        sorry_length = {}
        for sorry in sorrygifs:
            sorry_dict[sorry.api_name] = sorry.example
            sorry_name[sorry.api_name] = sorry.name
            sorry_length[sorry.api_name] = len(sorry.example.split("|"))
        receive_msg = receive["message"].replace("/gif", "", 1).strip()
        if receive_msg == "list":
            msg = ""
            for (k, v) in sorry_dict.items():
                msg = msg + "{}: {}({})\n".format(k, sorry_name[k], sorry_length[k])
        else:
            now_template = ""
            for (k, v) in sorry_dict.items():
                if receive_msg.find(k) == 0:
                    now_template = k
                    break
            if (not receive_msg) or receive_msg == "help":
                msg = " /gif list : 目前可用模板\n/gif $template example : 查看模板$template的样例\n/gif $template $msg0|$msg1|... : 按照$msg0,$msg1...生成沙雕GIF\nPowered by sorry.xuty.tk"
            elif not now_template.strip():
                msg = "未能找到对应模板，请确认后输入。"
            else:
                receive_msg = receive_msg.replace(now_template, "", 1).strip()
                if receive_msg == "example":
                    msg = sorry_dict[now_template]
                else:
                    msgs = receive_msg.split("|")
                    cnt = 0
                    gen_data = {}
                    for sentence in msgs:
                        sentence = sentence.strip()
                        if sentence == "":
                            continue
                        gen_data[str(cnt)] = sentence
                        logging.debug("sentence#%s:%s" % (cnt, sentence))
                        cnt += 1
                    if cnt == 0:
                        msg = "至少包含一条字幕消息"
                    else:
                        logging.debug("gen_data:%s" % (json.dumps(gen_data)))
                        url = SORRY_BASE_URL + "/api/%s/make" % (now_template)
                        url = SORRY_BASE_URL + "/%s/make" % (now_template)
                        try:
                            s = requests.post(
                                url=url, data=json.dumps(gen_data), timeout=2
                            )
                            bs = BeautifulSoup(s.text, "lxml")
                            a = bs.find_all("a")[0]
                            img_url = SORRY_BASE_URL + a.attrs["href"]
                            logging.debug("img_url:%s" % (img_url))
                            msg = "[CQ:image,cache=0,file=" + img_url + "]"
                        except Exception as e:
                            msg = "SORRY API ERROR:%s" % (type(e))
                            reply_action = reply_message_action(receive, msg)
                            action_list.append(reply_action)
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
