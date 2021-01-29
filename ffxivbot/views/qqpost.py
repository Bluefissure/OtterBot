import hmac
import json
import logging
import os
import time
import traceback

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt

from FFXIV import settings
from ffxivbot.consumers import PikaPublisher
from ffxivbot.models import QQBot, QQGroup


FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", settings.BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)
logging.basicConfig(format="%(levelname)s:%(message)s", level=logging.DEBUG)
LOGGER = logging.getLogger(__name__)


@csrf_exempt
def qqpost(req):
    try:
        # print("first request headers:")
        # print(req.META)
        receive = json.loads(req.body.decode())
        receive["reply_api_type"] = "http"
        text_data = json.dumps(receive)
        self_id = received_sig = req.META.get("HTTP_X_SELF_ID", "NULL")
        # print("=============")
        # print(self_id)
        # print("=============")
        error_msg = "Request not handled"
        try:
            bot = QQBot.objects.get(user_id=self_id)
            assert bot.api_post_url
        except QQBot.DoesNotExist:
            # print("bot {} does not exist".format(self_id))
            error_msg = "Bot {} does not exist".format(self_id)
        except AssertionError:
            # print("bot {} does not provide api url".format(self_id))
            error_msg = "Bot {} does not provide api url".format(self_id)
        else:
            pub = PikaPublisher()
            sig = hmac.new(str(bot.access_token).encode(), req.body, 'sha1').hexdigest()
            received_sig = req.META.get("HTTP_X_SIGNATURE", "NULL")[len('sha1='):]
            # print(req.META)
            # print("sig:{}\nreceived_sig:{}".format(sig, received_sig))
            if (sig == received_sig):
                # print("QQBot {}:{} authencation success".format(bot, self_id))
                if "post_type" in receive.keys():
                    bot.event_time = int(time.time())
                    bot.save(update_fields=["event_time"])
                    config = json.load(open(CONFIG_PATH, encoding="utf-8"))
                    already_reply = False
                    try:
                        self_id = receive["self_id"]
                        if "message" in receive.keys():
                            priority = 1
                            if isinstance(receive["message"], list):
                                tmp_msg = ""
                                for msg_seg in receive["message"]:
                                    if msg_seg["type"] == "text":
                                        tmp_msg += msg_seg["data"]["text"]
                                    elif msg_seg["type"] == "image":
                                        tmp_msg += "[CQ:image,file={}]".format(msg_seg["data"]["url"])
                                    elif "face" in msg_seg["type"]:
                                        tmp_msg += "[CQ:{},id={}]".format(msg_seg["type"], msg_seg["data"]["id"])
                                    elif msg_seg["type"] == "at":
                                        tmp_msg += "[CQ:at,qq={}]".format(msg_seg["data"]["qq"])
                                receive["message"] = tmp_msg
                            if receive["message"].startswith("/") or receive[
                                "message"
                            ].startswith("\\"):
                                # print(receive["message"])
                                priority += 1
                                bot.save(update_fields=["event_time"])
                                receive["consumer_time"] = time.time()
                                text_data = json.dumps(receive)
                                pub.send(text_data, priority)
                                return HttpResponse("Request sent to MQ", status=200)
                            else:
                                push_to_mq = False
                                if "group_id" in receive:
                                    group_id = receive["group_id"]
                                    (group, group_created) = QQGroup.objects.get_or_create(
                                        group_id=group_id
                                    )
                                    push_to_mq = "[CQ:at,qq={}]".format(self_id) in receive[
                                        "message"
                                    ] or (
                                                         (group.repeat_ban > 0)
                                                         or (group.repeat_length > 1 and group.repeat_prob > 0)
                                                 )
                                    # push_to_mq = "[CQ:at,qq={}]".format(self_id) in receive["message"]
                                if push_to_mq:
                                    receive["consumer_time"] = time.time()
                                    text_data = json.dumps(receive)
                                    pub.send(text_data, priority)
                                    return HttpResponse("Request sent to MQ", status=200)
                            return HttpResponse("Request message omitted", status=200)

                        if receive["post_type"] == "request" or receive["post_type"] == "event":
                            priority = 3
                            text_data = json.dumps(receive)
                            pub.send(text_data, priority)
                            return HttpResponse("Request sent to MQ", status=200)

                    except Exception as e:
                        traceback.print_exc()
                else:
                    bot.api_time = int(time.time())
                    bot.save(update_fields=["api_time"])
                    if int(receive["retcode"]) != 0:
                        if int(receive["retcode"]) == 1 and receive["status"] == "async":
                            print("API waring:" + text_data)
                        else:
                            print("API error:" + text_data)
                    if "echo" in receive.keys():
                        echo = receive["echo"]
                        LOGGER.debug("echo:{} received".format(receive["echo"]))
                        if echo.find("get_group_member_list") == 0:
                            group_id = echo.replace("get_group_member_list:", "").strip()
                            try:
                                # group = QQGroup.objects.select_for_update().get(group_id=group_id)
                                group = QQGroup.objects.get(group_id=group_id)
                                member_list = (
                                    json.dumps(receive["data"]) if receive["data"] else "[]"
                                )
                                group.member_list = member_list
                                group.save(update_fields=["member_list"])
                                # await send_message("group", group_id, "群成员信息刷新成功")
                            except QQGroup.DoesNotExist:
                                print("QQGroup.DoesNotExist:{}".format(group_id))
                                return HttpResponse(status=200)
                            LOGGER.debug("group %s member updated" % (group.group_id))
                        if echo.find("get_group_list") == 0:
                            bot.group_list = json.dumps(receive["data"])
                            bot.save(update_fields=["group_list"])
                        if echo.find("get_friend_list") == 0:
                            # friend_list = echo.replace("get_friend_list:","").strip()
                            bot.friend_list = json.dumps(receive["data"])
                            bot.save(update_fields=["friend_list"])
                        if echo.find("get_version_info") == 0:
                            bot.version_info = json.dumps(receive["data"])
                            bot.save(update_fields=["version_info"])
                        if echo.find("get_status") == 0:
                            user_id = echo.split(":")[1]
                            if not receive["data"] or not receive["data"]["good"]:
                                print(
                                    "bot:{} not good at time:{}".format(
                                        user_id, int(time.time())
                                    )
                                )
                            else:
                                LOGGER.debug(
                                    "bot:{} Universal heartbeat at time:{}".format(
                                        user_id, int(time.time())
                                    )
                                )
                    # bot.save()
            else:
                print("QQBot {}:{} authencation failed".format(bot, self_id))
                return HttpResponse("Wrong HTTP_X_SIGNATURE", status=500)
        return HttpResponse(error_msg, status=500)
    except Exception as e:
        traceback.print_exc()
        # print("request body:")
        # print(req.body.decode())
        return HttpResponse("Server error:{}".format(type(e)), status=500)
