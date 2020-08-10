from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random


def QQCommand_donate(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        msg = "酷Q已跑路，暂时关闭赞助渠道\n本项目不含任何付费功能，赞助均为自愿进行。"
        # msg = [{"type":"text","data":{"text":"我很可爱(*╹▽╹*)请给我钱"}},
        #     {"type":"image","data":{"file":QQ_BASE_URL+"static/alipay.jpg"}},
        #     {"type":"image","data":{"file":QQ_BASE_URL+"static/redpack.png"}}]
        # msg = [{"type":"text","data":{"text":"我很可爱(*╹▽╹*)但是不要捐助辣獭獭买了好多零食吃"}}]
        #         msg = [
        #             {
        #                 "type": "share",
        #                 "data": {
        #                     "url": "https://afdian.net/@bluefissure",
        #                     "title": "选择赞助獭獭的方案 | 爱发电",
        #                     "content": "来看看Bluefissure为你的赞助准备了什么奖励吧！",
        #                     "image": QQ_BASE_URL + "static/dist/img/tata.jpg",
        #                 },
        #             }
        #         ]
        #         reply_action = reply_message_action(receive, msg)
        #         action_list.append(reply_action)

        #         msg = [{"type": "text", "data": {"text": "感谢名单：\n\
        # Pants\n\
        # 初八\n\
        # 布谷布谷星\n\
        # 寒寒\n\
        # 盖瓯露依斯\n\
        # 黄金瓜\n\
        # 爱发电用户_uPMm\n\
        # 朝山霰\n\
        # 奶油熊子炖菜\n\
        # 爱发电用户_cgM5\n\
        # 我需要治疗\n\
        # 爱发电用户_aAFp\n\
        # Kke\n\
        # BoluoMB\n\
        # Mrrrr光\n\
        # 黑黑白\n\
        # 神楽坂千鸟光\
        # "}}]
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
