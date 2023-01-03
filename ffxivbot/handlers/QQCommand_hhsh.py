from .QQUtils import *
from ffxivbot.models import *
import logging
import traceback
import requests


def QQCommand_hhsh(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        content = receive["message"].replace("/hhsh", "", 1).strip()
        api_url = "https://lab.magiconch.com/api/nbnhhsh/"
        r = requests.post(api_url + "guess", data={"text": content}, timeout=3)
        if r.status_code != 200:
            msg = "API Error: HTTP {}".format(r.status_code)
        else:
            j = r.json()
            msg = ""
            for item in j:
                if "name" in item and "trans" in item:
                    msg += "{}: {}\n".format(item["name"], " ".join(item["trans"]))
            if not msg:
                msg = "未能查询到所包含缩写内容\n请前往 https://lab.magiconch.com/nbnhhsh/ 贡献词条"
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc()
    return []
