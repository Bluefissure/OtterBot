from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import time

def QQCommand_comment(*args, **kwargs):
    try:
        QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]

        user_id = receive["user_id"]
        comment_content = receive["message"].replace("/comment","",1).strip()
        if comment_content!="":
            comment = Comment(left_by=str(user_id),content=comment_content)
            comment.left_time = int(time.time())
            comment.save()
            msg = "留言:\"{}\"添加成功".format(comment_content)
        else:
            msg = "请输入留言内容，点击 {} 查看留言簿".format('http://111.231.102.248/static/doc/comments.txt')
        
        
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
