from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import time
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync


def QQCommand_comment(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config.get("QQ_BASE_URL")
        ADMIN_ID = global_config.get("ADMIN_ID")
        ADMIN_BOT = global_config.get("ADMIN_BOT")
        action_list = []
        receive = kwargs["receive"]
        bot = kwargs["bot"]

        user_id = receive["user_id"]
        self_id = receive["self_id"]
        group_id = receive["group_id"] if receive["message_type"] == "group" else ""
        comment_content = receive["message"].replace("/comment", "", 1).strip()
        if comment_content.strip().find("reply") == 0 and int(user_id) == int(ADMIN_ID):
            msg_segs = comment_content.replace("reply", "", 1).strip().split(" ")
            while "" in msg_segs:
                msg_segs.remove("")
            comment_id = msg_segs[0]
            reply_content = msg_segs[1]
            comm = Comment.objects.get(id=comment_id)
            reply_bot = QQBot.objects.get(user_id=comm.bot_id)
            if comm.left_group:
                message = '留言#{}"{}"的回复如下：\n======\n{}\n======\n[CQ:at,qq={}]'.format(
                    comm.id, comm.content, reply_content, comm.left_by
                )
                jdata = {
                    "action": "send_group_msg",
                    "params": {"group_id": comm.left_group, "message": message},
                }
            else:
                jdata = {
                    "action": "send_private_msg",
                    "params": {"user_id": comm.left_by, "message": message},
                }
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(
                reply_bot.api_channel_name,
                {"type": "send.event", "text": json.dumps(jdata)},
            )
            comm.reply = reply_content
            comm.save(update_fields=["reply"])
        elif comment_content != "":
            comment = Comment(
                left_by=str(user_id),
                content=comment_content,
                left_group=group_id,
                bot_id=self_id,
            )
            comment.left_time = int(time.time())
            comment.save()
            msg = '留言#{}:"{}"添加成功'.format(comment.id, comment.content)
            if ADMIN_ID:
                message = "Comment#{} from {} {}:\n{}".format(
                    comment.id, user_id, group_id, comment.content
                )
                admin_bot = QQBot.objects.get(user_id=ADMIN_BOT)
                jdata = {
                    "action": "send_private_msg",
                    "params": {"user_id": ADMIN_ID, "message": message},
                }
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(
                    admin_bot.api_channel_name,
                    {"type": "send.event", "text": json.dumps(jdata)},
                )
        else:
            msg = "请输入留言内容"

        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
