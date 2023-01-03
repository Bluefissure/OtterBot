from .QQUtils import *
from ffxivbot.models import *
import logging
import requests
import urllib
import base64


def QQCommand_tex(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]

        msg = ""
        receive_msg = receive["message"].replace("/tex", "", 1).strip()
        if receive_msg == "":
            msg = "/tex $tex：渲染公式$tex\n/tex /inlinemode $tex：行内模式"
        else:
            # print(receive_msg)
            tex_msg = urllib.parse.quote(receive_msg)
            # print(tex_msg)
            url = "http://mathurl.com/render.cgi?{}".format(tex_msg)
            # print(url)
            r = requests.get(url, timeout=5)
            b64str = base64.b64encode(r.content).decode()
            msg = "[CQ:image,file=base64://{}]".format(b64str)
        if msg:
            reply_action = reply_message_action(receive, msg)
            action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
