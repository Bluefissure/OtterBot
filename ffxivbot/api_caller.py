import base64
import json
import time
import os
import re
import requests
from channels.layers import get_channel_layer
from channels.exceptions import StopConsumer
from asgiref.sync import async_to_sync
from .models import QQGroup, QQBot, QQUser


class ApiCaller(object):
    def __init__(self, bot):
        self.bot = bot
        self.channel_layer = get_channel_layer()

    def handle_message(self, message):
        bot = self.bot
        new_message = message
        if isinstance(message, list):
            new_message = []
            for idx, msg in enumerate(message):
                if msg["type"] == "share" and bot.share_banned:
                    share_data = msg["data"]
                    new_message.append(
                        {
                            "type": "text",
                            "data": {
                                "text": "{}\n{}\n{}".format(
                                    share_data["title"],
                                    share_data["content"],
                                    share_data["url"],
                                )
                            },
                        }
                    )
                else:
                    new_message.append(msg)
        return new_message

    def call_api(self, action, params, echo=None, **kwargs):
        bot = self.bot
        if "async" not in action and not echo:
            action = action + "_async"
        if "send_" in action and "_msg" in action:
            params["message"] = self.handle_message(params["message"])
        jdata = {"action": action, "params": params}
        if echo:
            jdata["echo"] = echo
        post_type = kwargs.get("post_type", "websocket")
        if post_type == "websocket":
            async_to_sync(self.channel_layer.send)(
                bot.api_channel_name, {"type": "send.event", "text": json.dumps(jdata)}
            )
        elif post_type == "http":
            url = os.path.join(
                bot.api_post_url, "{}?access_token={}".format(action, bot.access_token)
            )
            headers = {"Content-Type": "application/json"}
            r = requests.post(
                url=url, headers=headers, data=json.dumps(params), timeout=5
            )
            if r.status_code != 200:
                print("HTTP Callback failed:")
                print(r.text)
        elif post_type == "wechat":
            self.third_party_wechat(action, params, echo, **kwargs)
        elif post_type == "tomon":
            self.third_party_tomon(action, params, echo, **kwargs)
        elif post_type == "iotqq":
            self.third_party_iotqq(action, params, echo, **kwargs)
        else:
            LOGGER.error("Unsupported protocol: {}".format(post_type))

    def update_group_member_list(self, group_id, **kwargs):
        bot = self.bot
        self.call_api(
            "get_group_member_list",
            {"group_id": group_id},
            "get_group_member_list:%s" % (group_id),
            **kwargs,
        )

    def send_message(self, target_type, uid, message, **kwargs):
        if target_type == "group":
            self.call_api(
                "send_group_msg", {"group_id": uid, "message": message}, **kwargs
            )
        if target_type == "discuss":
            self.call_api(
                "send_discuss_msg", {"discuss_id": uid, "message": message}, **kwargs
            )
        if target_type == "private":
            self.call_api(
                "send_private_msg", {"user_id": uid, "message": message}, **kwargs
            )

    def third_party_wechat(self, action, params, echo=None, **kwargs):
        bot = self.bot
        print("Calling  wechat api:{}".format(action))

        def req_url(params):
            url = "https://ex-api.botorange.com/message/send"
            headers = {"Content-Type": "application/json"}
            print("params:{}".format(json.dumps(params)))
            r = requests.post(
                url=url, headers=headers, data=json.dumps(params), timeout=5
            )
            if r.status_code != 200:
                print("Wechat HTTP Callback failed:")
                print(r.text)

        config = json.load(open(CONFIG_PATH, encoding="utf-8"))
        params["chatId"] = kwargs.get("chatId", "")
        params["token"] = config.get("WECHAT_TOKEN", "")
        if "send_" in action and "_msg" in action:
            if isinstance(params["message"], str):
                text = params["message"]
                at = re.finditer(r"\[CQ:at,qq=(.*)\]", text)
                if at:
                    params["mention"] = [at_m.group(1) for at_m in at]
                text = re.sub(r"\[CQ:at,qq=(.*)\]", "", text)
                img_r = r"\[CQ:image,file=(.*?)(?:\]|,.*?\])"
                img_m = re.search(img_r, text)
                if img_m:  # FIXME: handle text & img message
                    params["messageType"] = 1
                    params["payload"] = {"url": img_m.group(1)}
                else:
                    params["messageType"] = 0
                    params["payload"] = {"text": text.strip()}
                req_url(params)
            else:
                for msg_seg in params["message"]:
                    if msg_seg["type"] == "image":
                        params["messageType"] = 1
                        params["payload"] = {"url": msg_seg["data"]["file"]}
                        req_url(params)
                    elif msg_seg["type"] == "text":
                        params["messageType"] = 0
                        params["payload"] = {"text": msg_seg["data"]["text"].strip()}
                        req_url(params)
                    time.sleep(1)

    def third_party_tomon(self, action, params, echo=None, **kwargs):
        base_url = "https://beta.tomon.co/api/v1"
        bot = self.bot
        channel_id = kwargs.get("channel_id")
        group_id = params.get("group_id")
        headers = {
            "Authorization": "Bearer {}".format(bot.tomon_bot.all()[0].token),
        }
        if "send_" in action and "_msg" in action:
            print("Tomon Message >>> {}".format(params["message"]))
            attachments = []
            if isinstance(params["message"], str):
                message = params["message"]
                message = re.sub(r"\[CQ:at,qq=(.*?)\]", "<@\g<1>>", message)
                # print("message 1 >>> {}".format(message))
                img_pattern = r"\[CQ:image,(?:cache=.,)?file=(.*?)(?:\]|,.*?\])"
                m = re.search(img_pattern, message)
                if m:
                    attachments.append({"url": m.group(1)})
                    message = re.sub(img_pattern, "", message)
                    # print("message 2 >>> {}".format(message))
            elif isinstance(params["message"], list):
                message = ""
                for msg in params["message"]:
                    if msg["type"] == "text":
                        message += msg["data"]["text"]
                    elif msg["type"] == "image":
                        img_url = msg["data"]["file"]
                        attachments.append({"url": img_url})
                    elif msg["type"] == "share":
                        share_data = msg["data"]
                        message += "{}\n{}\n{}\n".format(
                            share_data["title"],
                            share_data["content"],
                            share_data["url"],
                        )
            nonce = kwargs.get("nonce", "")
            data = {"content": message, "nonce": nonce}
            url = base_url + "/channels/{}/messages".format(channel_id)
            if attachments:
                payload = {"payload_json": json.dumps(data)}
                if attachments[0]["url"].startswith("base64://"):
                    img_format = "jpg"
                    img_content = base64.b64decode(
                        attachments[0]["url"].replace("base64://", "", 1)
                    )
                else:
                    img_format = attachments[0]["url"].split(".")[-1]
                    original_image = requests.get(attachments[0]["url"], timeout=3)
                    img_content = original_image.content
                files = [("image.{}".format(img_format), img_content)]
                r = requests.post(
                    headers=headers, url=url, files=files, data=payload, timeout=30,
                )
                if r.status_code != 200:
                    print("Tomon HTTP Callback failed:")
                    print(r.text)
                return
            headers.update({"Content-Type": "application/json"})
            r = requests.post(
                url=url, headers=headers, data=json.dumps(data), timeout=3
            )
            if r.status_code != 200:
                print("Tomon HTTP Callback failed:")
                print(r.text)
        if action == "get_group_member_list":
            url = base_url + "/guilds/{}/roles".format(group_id)
            headers.update({"Content-Type": "application/json"})
            r = requests.get(url=url, headers=headers, timeout=3)
            if r.status_code != 200:
                print("Tomon HTTP Callback failed:")
                print(r.text)
                return
            group, _ = QQGroup.objects.get_or_create(group_id=group_id)
            group.member_list = json.dumps(r.json())
            group.save(update_fields=["member_list"])

    def third_party_iotqq(self, action, params, echo=None, **kwargs):
        bot = self.bot
        headers = {
            "Content-Type": "application/json",
        }
        if bot.iotqq_auth:
            headers.update(
                {
                    "Authorization": "Basic "
                    + base64.b64encode(bot.iotqq_auth.encode()).decode()
                }
            )
        if "send_" in action and "_msg" in action:
            send_params = (
                ("qq", bot.user_id),
                ("funcname", "SendMsg"),
            )
            send_data = {
                "toUser": params["group_id"],
                "sendToType": 2,
                "sendMsgType": "TextMsg",
                "content": "",
                "groupid": 0,
                "atUser": 0,
                "replayInfo": None,
            }
            message = params["message"]
            attachments = []
            if isinstance(params["message"], str):
                message = re.sub(r"\[CQ:at,qq=(.*)\]", "[ATUSER(\g<1>)]", message)
                img_pattern = r"\[CQ:image,(?:cache=.,)?file=(.*?)(?:\]|,.*?\])"
                m = re.search(img_pattern, message)
                if m:
                    attachments.append({"url": m.group(1)})
                    # message = re.sub(img_pattern, " \g<1> ", message)
                    message = re.sub(img_pattern, "", message)
            elif isinstance(params["message"], list):
                message = ""
                for msg in params["message"]:
                    if msg["type"] == "text":
                        message += msg["data"]["text"]
                    elif msg["type"] == "image":
                        img_url = msg["data"]["file"]
                        attachments.append({"url": img_url})
                    elif msg["type"] == "share":  # TODO: change to actual share
                        share_data = msg["data"]
                        message += "{}\n{}\n{}\n".format(
                            share_data["title"],
                            share_data["content"],
                            share_data["url"],
                        )
            if attachments:
                send_data["sendMsgType"] = "PicMsg"
                send_data["picUrl"] = attachments[0]["url"]
                send_data["picBase64Buf"] = ""
                send_data["fileMd5"] = ""
            if isinstance(message, str) and len(message) > 960:
                message = message[:950] + "\n......"
            send_data["content"] = message
            print("IOTQQ send_data:")
            print(json.dumps(send_data, indent=4))
            r = requests.post(
                bot.iotqq_url,
                headers=headers,
                params=send_params,
                json=send_data,
                timeout=10,
            )
            if r.status_code != 200:
                print("IOTQQ HTTP Callback failed:")
                print(r.text)

