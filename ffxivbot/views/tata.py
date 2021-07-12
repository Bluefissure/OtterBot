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
    pattern = re.compile(
        r"^(?:https?://)?(?P<host>[^:/]+)(?::(?P<port>\d+))?(?:/(?P<path>.*))?$"
    )
    matches = pattern.match(web_base_url)
    if matches:
        host = matches.group("host")
        port = matches.group("port") if matches.group("port") else 80
        path = matches.group("path") if matches.group("path") else ""
    if use_tls and port == 80:
        port = 443
    if path != "" and not path.endswith("/"):
        path = path + "/"
    return {"host": host, "port": port, "path": path, "use_tls": use_tls}


def generate_bot_conf(
    bot: QQBot,
    client: str,
    host: str = "localhost",
    port: int = 80,
    path: str = "",
    use_tls: bool = False,
):
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
        ws_reverse_url = '{}'.format(ws_url)
        if bot.api_post_url:
            use_http = "0.0.0.0"
            post_url = "  - url: '{}'".format(http_url)
            secret   = "    secret: '{}'".format(bot.access_token)
            disable_ws_reverse = "true"
        else:
            use_http = "127.0.0.1"
            post_url = "#  - url: ''"
            secret   = "#    secret: ''"
            disable_ws_reverse = "false"
        conf = (
            bot.user_id,
            bot.access_token,
            use_http,
            post_url,
            secret,
            disable_ws_reverse,
            ws_reverse_url,
        )
        bot_conf = """account: # 账号相关
  uin: {} # QQ账号
  password: '' # 密码为空时使用扫码登录
  encrypt: false  # 是否开启密码加密
  status: 0      # 在线状态 请参考 https://docs.go-cqhttp.org/guide/config.html#在线状态
  relogin: # 重连设置
    delay: 3   # 首次重连延迟, 单位秒
    interval: 3   # 重连间隔
    max-times: 0  # 最大重连次数, 0为无限制

  # 是否使用服务器下发的新地址进行重连
  # 注意, 此设置可能导致在海外服务器上连接情况更差
  use-sso-address: true

heartbeat:
  # 心跳频率, 单位秒
  # -1 为关闭心跳
  interval: 5

message:
  # 上报数据类型
  # 可选: string,array
  post-format: string
  # 是否忽略无效的CQ码, 如果为假将原样发送
  ignore-invalid-cqcode: false
  # 是否强制分片发送消息
  # 分片发送将会带来更快的速度
  # 但是兼容性会有些问题
  force-fragment: false
  # 是否将url分片发送
  fix-url: false
  # 下载图片等请求网络代理
  proxy-rewrite: ''
  # 是否上报自身消息
  report-self-message: false
  # 移除服务端的Reply附带的At
  remove-reply-at: false
  # 为Reply附加更多信息
  extra-reply-data: false

output:
  # 日志等级 trace,debug,info,warn,error
  log-level: warn
  # 是否启用 DEBUG
  debug: false # 开启调试模式

# 默认中间件锚点
default-middlewares: &default
  # 访问密钥, 强烈推荐在公网的服务器设置
  access-token: {}
  # 事件过滤器文件目录
  filter: ''
  # API限速设置
  # 该设置为全局生效
  # 原 cqhttp 虽然启用了 rate_limit 后缀, 但是基本没插件适配
  # 目前该限速设置为令牌桶算法, 请参考:
  # https://baike.baidu.com/item/%E4%BB%A4%E7%89%8C%E6%A1%B6%E7%AE%97%E6%B3%95/6597000?fr=aladdin
  rate-limit:
    enabled: false # 是否启用限速
    frequency: 1  # 令牌回复频率, 单位秒
    bucket: 1     # 令牌桶大小

database: # 数据库相关设置
  leveldb:
    # 是否启用内置leveldb数据库
    # 启用将会增加10-20MB的内存占用和一定的磁盘空间
    # 关闭将无法使用 撤回 回复 get_msg 等上下文相关功能
    enable: true

# 连接服务列表
servers:
  # 添加方式，同一连接方式可添加多个，具体配置说明请查看文档
  #- http: # http 通信
  #- ws:   # 正向 Websocket
  #- ws-reverse: # 反向 Websocket
  #- pprof: #性能分析服务器
  # HTTP 通信设置
  - http:
      # 服务端监听地址
      host: {}
      # 服务端监听端口
      port: 5700
      # 反向HTTP超时时间, 单位秒
      # 最小值为5，小于5将会忽略本项设置
      timeout: 5
      middlewares:
        <<: *default # 引用默认中间件
      # 反向HTTP POST地址列表
      post:
      {} # 地址
      {} # 密钥
  # 反向WS设置
  - ws-reverse:
      # 是否禁用当前反向WS服务
      disabled: {}
      # 反向WS Universal 地址
      # 注意 设置了此项地址后下面两项将会被忽略
      universal: {}
      # 反向WS API 地址
      api: 
      # 反向WS Event 地址
      event: 
      # 重连间隔 单位毫秒
      reconnect-interval: 3000
      middlewares:
        <<: *default # 引用默认中间件
""".format(
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
            bb["owner_id"] = bot.owner_id
        else:

            def mask_id(user_id):
                mid = len(user_id) // 2
                return user_id[: mid - 2] + "*" * 4 + user_id[mid + 2 :]

            bb["user_id"] = mask_id(bot.user_id)
            bb["owner_id"] = mask_id(bot.owner_id)
        bb["group_num"] = group_num
        bb["friend_num"] = friend_num
        bb["coolq_edition"] = coolq_edition
        bb["online"] = time.time() - bot.event_time < 300
        bb["id"] = bot.id
        bb["public"] = bot.public
        bb["autoinvite"] = bot.auto_accept_invite
        bb["autofriend"] = bot.auto_accept_friend
        bot_list.append(bb)
    return ren2res("tata.html", req, {"bots": bot_list})
