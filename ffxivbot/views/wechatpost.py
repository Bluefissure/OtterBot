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
def wechatpost(req):
    pub = PikaPublisher()
    try:
        print("wechat request headers:")
        print(req.META)
        receive = json.loads(req.body.decode())
        receive["reply_api_type"] = "wechat"
        text_data = json.dumps(receive)
        config = json.load(open(CONFIG_PATH, encoding="utf-8"))
        self_id = config.get("ADMIN_BOT", "")
        admin_id = config.get("ADMIN_ID", "")
        admin_bot_id = config.get("ADMIN_BOT", "")
        error_msg = "Request not handled"
        try:
            bot = QQBot.objects.get(user_id=self_id)
        except QQBot.DoesNotExist:
            print("bot {} does not exist".format(self_id))
            error_msg = "Bot {} does not exist".format(self_id)
        except AssertionError:
            print("bot {} does not provide api url".format(self_id))
            error_msg = "Bot {} does not provide api url".format(self_id)
        else:
            token = config.get("WECHAT_TOKEN", "")
            received_token = receive["data"]["token"]
            if (not token or token != received_token):
                print("WechatBot {}:{} authencation failed".format(bot, self_id))
                return HttpResponse("Wrong TOKEN", status=500)
            
            if "data" in receive.keys():
                bot.event_time = int(time.time())
                bot.save(update_fields=["event_time"])
                already_reply = False
                try:
                    chatId = receive["data"]["chatId"]
                    msgType = receive["data"]["type"]
                    if int(msgType) == 7:
                        priority = 1
                        message = receive["data"]["payload"]["text"]
                        receive["chatId"] = receive["data"]["chatId"]
                        receive["time"] = int(receive["data"]["timestamp"]) / 1000
                        receive["post_type"] = "message"
                        receive["message"] = message
                        receive["user_id"] = receive["data"]["contactId"]
                        receive["self_id"] = admin_bot_id
                        receive["message_type"] = "private"
                        if receive["data"].get("roomId", ""):
                            receive["message_type"] = "group"
                            receive["group_id"] = receive["data"]["roomId"]
                        else:
                            receive["message_type"] = "private"
                        if message.startswith("/") or message.startswith("\\"):
                            priority += 1
                            bot.save(update_fields=["event_time"])
                            receive["consumer_time"] = time.time()
                            text_data = json.dumps(receive)
                            pub.send(text_data, priority)
                            print("data:{}".format(text_data))
                            return HttpResponse("Request sent to MQ", status=200)
                        else:
                            print("no / data:{}".format(text_data))
                            push_to_mq = False
                            if "group_id" in receive:
                                group_id = receive["group_id"]
                                (group, group_created) = QQGroup.objects.get_or_create(
                                    group_id=group_id
                                )
                                mentions = receive["data"]["payload"].get("mention", [])
                                print("mentions:{}".format(mentions))
                                print("matched:{}".format(mentions and mentions[0] == bot.wechat_id))
                                receive["self_wechat_id"] = bot.wechat_id
                                push_to_mq = (mentions and mentions[0] == bot.wechat_id) or (
                                                        (group.repeat_ban > 0)
                                                        or (group.repeat_length > 1 and group.repeat_prob > 0)
                                                )
                                print("push_to_mq:{}".format(push_to_mq))
                                # push_to_mq = "[CQ:at,qq={}]".format(self_id) in receive["message"]
                            if push_to_mq:
                                receive["consumer_time"] = time.time()
                                text_data = json.dumps(receive)
                                pub.send(text_data, priority)
                                return HttpResponse("Request sent to MQ", status=200)
                        return HttpResponse("Request message omitted", status=200)

                    # if receive["post_type"] == "request" or receive["post_type"] == "event":
                    #     priority = 3
                    #     text_data = json.dumps(receive)
                    #     pub.send(text_data, priority)
                    #     return HttpResponse("Request sent to MQ", status=200)

                except Exception as e:
                    traceback.print_exc()
        return HttpResponse(error_msg, status=500)
    except Exception as e:
        traceback.print_exc()
        # print("request body:")
        # print(req.body.decode())
        return HttpResponse("Server error:{}".format(type(e)), status=500)
    return HttpResponse("Uknown server error.", status=500)
