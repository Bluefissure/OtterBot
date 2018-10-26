from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random
import time

class QQCommand_comment(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_comment, self).__init__()
    def __call__(self, **kwargs):
        try:
            QQ_BASE_URL = kwargs["global_config"]["QQ_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]

            user_id = receive["user_id"]
            comment_content = receive["message"].replace("/comment","",1)
            comment = Comment(left_by=str(user_id),content=comment_content)
            comment.left_time = int(time.time())
            comment.save()
            msg = "留言:\"{}\"添加成功".format(comment_content)
            
            reply_action = self.reply_message_action(receive, msg)
            action_list.append(reply_action)
            return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)
