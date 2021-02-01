from django.http import HttpResponse, JsonResponse

from FFXIV import settings
from ffxivbot.models import *
from .ren2res import ren2res
import json
import os
import re
import yaml

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)


def generate_web_base(web_base_url: str) -> dict:
    host = "localhost"
    port = 80
    path = ""
    use_tls = False
    if web_base_url.startswith("https://"):
        use_tls = True
    pattern = re.compile(r'^(?:https?://)?(?P<host>[^:/]+)(?::(?P<port>\d+))?(?:/(?P<path>.*))?$')
    matches = pattern.match(web_base_url)
    if matches:
        host = matches.group("host")
        port = matches.group("port") if matches.group("port") else 80
        path = matches.group("path") if matches.group("path") else ""
    if use_tls and port == 80:
        port = 443
    if path != "" and not path.endswith("/"):
        path = path + "/"
    return {
        "host": host,
        "port": port,
        "path": path,
        "use_tls": use_tls
    }


def generate_bot_conf(bot: QQBot, client: str, host: str = "localhost", port: int = 80, path: str = "", use_tls: bool = False):
    bot_conf = {"error": "Unsupported client."}
    if use_tls:
        ws_url = f"wss://{host}:{port}/{path}ws/"
        http_url = f"https://{host}:{port}/{path}http/"
    else:
        ws_url = f"ws://{host}:{port}/{path}ws/"
        http_url = f"http://{host}:{port}/{path}http/"
    if client == "Mirai":
        bot_conf = {
            "proxy": "",
            "bots": {
                str(bot.user_id): {
                    "cacheImage": True,
                    "cacheRecord": True,
                    "heartbeat": {"enable": True, "interval": 15000,},
                    "http": {
                        "enable": False,
                        "host": "0.0.0.0",
                        "port": 5700,
                        "accessToken": "",
                        "postUrl": "",
                        "postMessageFormat": "string",
                        "secret": "",
                    },
                    "ws_reverse": [
                        {
                            "enable": True,
                            "postMessageFormat": "string",
                            "reverseHost": host,
                            "reversePort": port,
                            "accessToken": "",
                            "reversePath": f"/{path}ws",
                            "reverseApiPath": f"/{path}api",
                            "reverseEventPath": f"/{path}event",
                            "useUniversal": True,
                            "useTLS": use_tls,
                            "reconnectInterval": 3000,
                        }
                    ],
                    "ws": {
                        "enable": False,
                        "postMessageFormat": "string",
                        "accessToken": "SECRET",
                        "wsHost": "0.0.0.0",
                        "wsPort": 8080,
                    },
                },
            },
        }
        if bot.api_post_url:
            bot_conf["bots"][str(bot.user_id)]["http"]["enable"] = True
            bot_conf["bots"][str(bot.user_id)]["http"]["postUrl"] = http_url
            bot_conf["bots"][str(bot.user_id)]["http"]["secret"] = bot.access_token
            bot_conf["bots"][str(bot.user_id)]["ws_reverse"][0]["enable"] = False
        else:
            bot_conf["bots"][str(bot.user_id)]["ws_reverse"][0]["enable"] = True
            bot_conf["bots"][str(bot.user_id)]["ws_reverse"][0][
                "accessToken"
            ] = bot.access_token
        bot_conf = yaml.dump(bot_conf).encode()
    elif client == "YaYa":
        bot_conf = {
            "version": "1.0.5",
            "master": 12345678,
            "debug": True,
            "cache": {
                "database": False,
                "image": False,
                "record": False,
                "video": False,
            },
            "heratbeat": {"enable": True, "interval": 10000,},
            "bots": [
                {
                    "bot": 0,
                    "websocket": [
                        {
                            "name": "WSS EXAMPLE",
                            "enable": False,
                            "host": "127.0.0.1",
                            "port": 6700,
                            "access_token": "",
                            "post_message_format": "string",
                        },
                    ],
                    "websocket_reverse": [
                        {
                            "name": "WSC EXAMPLE",
                            "enable": True,
                            "url": "ws://127.0.0.1:8080/ws",
                            "api_url": "ws://127.0.0.1:8080/api",
                            "event_url": "ws://127.0.0.1:8080/event",
                            "use_universal_client": True,
                            "access_token": "",
                            "post_message_format": "string",
                            "reconnect_interval": 3000,
                        },
                    ],
                    "http": [
                        {
                            "name": "HTTP EXAMPLE",
                            "enable": False,
                            "host": "127.0.0.1",
                            "port": 5700,
                            "access_token": "",
                            "post_url": "http://127.0.0.1/plugin",
                            "secret": "",
                            "time_out": 0,
                            "post_message_format": "string",
                        },
                    ],
                },
            ],
        }
        bot_conf["bots"][0]["bot"] = int(bot.user_id)
        bot_conf["master"] = int(bot.owner_id)
        if bot.api_post_url:
            bot_conf["bots"][0]["http"][0]["name"] = "tata"
            bot_conf["bots"][0]["http"][0]["enable"] = True
            bot_conf["bots"][0]["http"][0]["post_url"] = http_url
            bot_conf["bots"][0]["http"][0]["secret"] = bot.access_token
            bot_conf["bots"][0]["websocket_reverse"][0]["enable"] = False
        else:
            bot_conf["bots"][0]["websocket_reverse"][0]["name"] = "tata"
            bot_conf["bots"][0]["websocket_reverse"][0]["enable"] = True
            bot_conf["bots"][0]["websocket_reverse"][0]["url"] = ws_url
            bot_conf["bots"][0]["websocket_reverse"][0][
                "access_token"
            ] = bot.access_token
        bot_conf = yaml.dump(bot_conf).encode()
    elif client == "Go-cqhttp":
        if bot.api_post_url:
            use_http = "true"
            use_ws = "false"
            post_url = '{{"{}":"{}"}}'.format(http_url, bot.access_token)
            ws_reverse_url = ""
        else:
            use_http = "false"
            use_ws = "true"
            post_url = "{}"
            ws_reverse_url = '"{}"'.format(ws_url)
        conf = (bot.user_id, bot.access_token, use_http, post_url, use_ws, ws_reverse_url)
        bot_conf = """{{
    uin: {}
    password: ""
    encrypt_password: false
    password_encrypted: ""
    enable_db: true
    access_token: "{}"
    relogin: {{
        enabled: true
        relogin_delay: 3
        max_relogin_times: 0
    }}
    _rate_limit: {{
        enabled: false
        frequency: 1
        bucket_size: 1
    }}
    ignore_invalid_cqcode: false
    force_fragmented: false
    heartbeat_interval: 5
    http_config: {{
        enabled: {}
        host: 0.0.0.0
        port: 5700
        timeout: 0
        post_urls: {}
    }}
    ws_config: {{
        enabled: false
        host: 0.0.0.0
        port: 6700
    }}
    ws_reverse_servers: [
        {{
            enabled: {}
            reverse_url: {}
            reverse_api_url: ""
            reverse_event_url: ""
            reverse_reconnect_interval: 3000
        }}
    ]
    post_message_format: string
    use_sso_address: false
    debug: false
    log_level: ""
    web_ui: {{
        enabled: true
        host: 127.0.0.1
        web_ui_port: 9999
        web_input: false
    }}
}}""".format(
            *conf
        )
    elif client == "OICQ":
        access_token = '"{}"'.format(bot.access_token)
        if bot.api_post_url:
            use_http = "true"
            post_url = '"{}",'.format(http_url)
            ws_reverse_url = ""
        else:
            use_http = "false"
            post_url = ""
            ws_reverse_url = '"{}",'.format(ws_url)
        conf = (use_http, access_token, access_token, post_url, ws_reverse_url)
        # print(conf)
        bot_conf = """"use strict";
module.exports = {{
    general: {{
        platform:           2,
        ignore_self:        true,
        resend:             true,
        debug:              false,
        use_cqhttp_notice:  true,

        host:               "0.0.0.0",
        port:               5700,
        use_http:           {},
        use_ws:             false,
        access_token:       {},
        secret:             {},
        post_timeout:       30,
        post_message_format:"string",
        enable_heartbeat:   false,
        heartbeat_interval: 15000,
        rate_limit_interval:500,
        event_filter:       "",
        post_url: [
            {}
        ],
        ws_reverse_url: [ 
            {}
        ],
        ws_reverse_reconnect_interval: 3000,
    }}
}};""".format(
            *conf
        )
    return bot_conf


def get_bot_version(obj: dict):
    ver = ""
    if obj.get("go-cqhttp"):
        ver = "Go"
    elif obj.get("app_name"):
        name = obj.get("app_name")
        if name.find("YaYa") != -1:
            ver = "XQ"
        elif name.find("onebot-mirai") != -1:
            ver = "Mirai"
        elif name.find("cqhttp-mirai") != -1:
            ver = "Mirai\n(Low)"
    elif obj.get("name"):
        name = obj.get("name")
        if name.find("oicq") != -1:
            ver = "OICQ"
    elif obj.get("coolq_directory"):
        dire = obj.get("coolq_directory")
        if dire.find("CQHTTPMirai") != -1:
            ver = "Mirai\n(Low)"
        if dire.find("jre\\bin") != -1:
            ver = "Mirai\n(Native)"
    return ver


def tata(req):
    if req.is_ajax() and req.method == "POST":
        res_dict = {"response": "No response."}
        optype = req.POST.get("optype")
        if settings.DEBUG:
            print("optype:{}".format(optype))
        if optype == "add_or_update_bot":
            botName = req.POST.get("botName")
            botID = req.POST.get("botID")
            ownerID = req.POST.get("ownerID")
            accessToken = req.POST.get("accessToken")
            tulingToken = req.POST.get("tulingToken")
            api_post_url = req.POST.get("api_post_url", "").strip()
            autoFriend = req.POST.get("autoFriend")
            autoInvite = req.POST.get("autoInvite")
            if len(botName) < 2:
                res_dict = {"response": "error", "msg": "机器人昵称太短"}
                return JsonResponse(res_dict)
            if len(accessToken) < 5:
                res_dict = {"response": "error", "msg": "Access Token太短"}
                return JsonResponse(res_dict)
            if not ownerID.strip():
                res_dict = {"response": "error", "msg": "领养者不能为空"}
                return JsonResponse(res_dict)
            bots = QQBot.objects.filter(user_id=botID)
            if not bots.exists():
                bot = QQBot(user_id=botID, access_token=accessToken)
                bot_created = True
            else:
                if bots[0].access_token != accessToken:
                    res_dict = {"response": "error", "msg": "Token错误，请确认后重试。"}
                    return JsonResponse(res_dict)
                bot = bots[0]
                bot_created = False
            if bot:
                bot.name = botName
                bot.owner_id = ownerID
                bot.tuling_token = tulingToken
                bot.api_post_url = api_post_url
                bot.auto_accept_friend = autoFriend and "true" in autoFriend
                bot.auto_accept_invite = autoInvite and "true" in autoInvite
                if len(QQBot.objects.all()) >= 200 and bot_created:
                    res_dict = {"response": "error", "msg": "机器人总数过多，请稍后再试"}
                    return JsonResponse(res_dict)
                bot.save()
                res_dict = {
                    "response": "success",
                    "msg": "{}({})".format(bot.name, bot.user_id)
                    + ("添加" if bot_created else "更新")
                    + "成功，Token为:",
                    "token": bot.access_token,
                }
            return JsonResponse(res_dict)
        bot_id = req.POST.get("id")
        token = req.POST.get("token")
        client = req.POST.get("client")
        if settings.DEBUG:
            print("bot_id:{} token:{} client:{}".format(bot_id, token, client))
        try:
            bot = QQBot.objects.get(id=bot_id, access_token=token)
        except Exception as e:
            if "QQBot matching query does not exist" in str(e):
                res_dict = {"response": "error", "msg": "Token错误，请确认后重试。"}
            else:
                res_dict = {"response": "error", "msg": str(e)}
            return JsonResponse(res_dict)
        if optype == "switch_public":
            bot.public = not bot.public
            bot.save()
            res_dict["response"] = "success"
        elif optype == "del_bot":
            bot.delete()
            res_dict["response"] = "success"
        elif optype == "download_conf":
            response = HttpResponse(content_type="application/octet-stream")
            response["Content-Disposition"] = 'attachment; filename="settings.yml"'
            config = json.load(open(CONFIG_PATH, encoding="utf-8"))
            web_base_url = config.get("WEB_BASE_URL", "xn--v9x.net")
            web_base = generate_web_base(web_base_url=web_base_url)
            bot_conf = generate_bot_conf(bot, client, **web_base)
            response.write(bot_conf)
            return response
        return JsonResponse(res_dict)

    bots = QQBot.objects.all()
    bot_list = []
    for bot in bots:
        bb = {}
        version_info = json.loads(bot.version_info)
        coolq_edition = get_bot_version(version_info)
        friend_list = json.loads(bot.friend_list)
        friend_num = len(friend_list) if friend_list else "-1"
        group_list = json.loads(bot.group_list)
        group_num = len(group_list) if group_list else -1
        bb["name"] = bot.name
        if bot.public:
            bb["user_id"] = bot.user_id
        else:
            mid = len(bot.user_id) // 2
            user_id = bot.user_id[: mid - 2] + "*" * 4 + bot.user_id[mid + 2 :]
            bb["user_id"] = user_id
        bb["group_num"] = group_num
        bb["friend_num"] = friend_num
        bb["coolq_edition"] = coolq_edition
        bb["owner_id"] = bot.owner_id
        bb["online"] = time.time() - bot.event_time < 300
        bb["id"] = bot.id
        bb["public"] = bot.public
        bb["autoinvite"] = bot.auto_accept_invite
        bb["autofriend"] = bot.auto_accept_friend
        bot_list.append(bb)
    return ren2res("tata.html", req, {"bots": bot_list})
