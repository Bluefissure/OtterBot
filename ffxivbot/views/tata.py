from django.http import HttpResponse, JsonResponse

from FFXIV import settings
from ffxivbot.models import *
from .ren2res import ren2res
import json, os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)

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
            elif len(accessToken) < 5:
                res_dict = {"response": "error", "msg": "Access Token太短"}
                return JsonResponse(res_dict)
            elif not ownerID.strip():
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
                else:
                    bot = bots[0]
                    bot_created = False
            if bot:
                bot.name = botName
                bot.owner_id = ownerID
                bot.tuling_token = tulingToken
                bot.api_post_url = api_post_url
                bot.auto_accept_friend = autoFriend and "true" in autoFriend
                bot.auto_accept_invite = autoInvite and "true" in autoInvite
                if len(QQBot.objects.all()) >= 250 and bot_created:
                    res_dict = {"response": "error", "msg": "机器人总数过多，请稍后再试"}
                    return JsonResponse(res_dict)
                bot.save()
                res_dict = {
                    "response": "success",
                    "msg": "{}({})".format(bot.name, bot.user_id) + ("添加" if bot_created else "更新") + "成功，Token为:",
                    "token": bot.access_token,
                }
            return JsonResponse(res_dict)
        else:
            bot_id = req.POST.get("id")
            token = req.POST.get("token")
            if settings.DEBUG:
                print("bot_id:{} token:{}".format(bot_id, token))
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
                response[
                    "Content-Disposition"
                ] = 'attachment; filename="{}.json"'.format(bot.user_id)
                config = json.load(open(CONFIG_PATH, encoding="utf-8"))
                web_base = config.get("WEB_BASE_URL", "xn--v9x.net")
                web_base = web_base.replace("https://", "")
                web_base = web_base.replace("http://", "")
                ws_url = "ws://" + os.path.join(web_base, "ws/")
                http_url = "http://" + os.path.join(web_base, "http/")
                bot_conf = json.loads(
                    '{\
                        "host": "0.0.0.0",\
                        "port": 5700,\
                        "use_http": false,\
                        "ws_host": "0.0.0.0",\
                        "ws_port": 6700,\
                        "use_ws": false,\
                        "ws_reverse_url": "",\
                        "ws_reverse_use_universal_client": true,\
                        "enable_heartbeat": true,\
                        "use_ws_reverse": "yes",\
                        "ws_reverse_reconnect_interval": 5000,\
                        "ws_reverse_reconnect_on_code_1000": "yes",\
                        "post_url": "",\
                        "access_token": "",\
                        "secret": "",\
                        "post_message_format": "string",\
                        "serve_data_files": false,\
                        "update_source": "github",\
                        "update_channel": "stable",\
                        "auto_check_update": false,\
                        "auto_perform_update": false,\
                        "thread_pool_size": 4,\
                        "server_thread_pool_size": 1,\
                        "show_log_console": false,\
                        "enable_backward_compatibility": true\
                    }'
                )
                if bot.api_post_url:
                    bot_conf["use_ws_reverse"] = False
                    bot_conf["post_url"] = http_url
                else:
                    bot_conf["use_ws_reverse"] = True
                    bot_conf["ws_reverse_url"] = ws_url
                bot_conf["access_token"] = bot.access_token
                bot_conf["secret"] = bot.access_token
                response.write(json.dumps(bot_conf, indent=4))
                return response
        return JsonResponse(res_dict)

    bots = QQBot.objects.all()
    bot_list = []
    for bot in bots:
        bb = {}
        version_info = json.loads(bot.version_info)
        coolq_edition = (
            version_info["coolq_edition"]
            if version_info and "coolq_edition" in version_info.keys()
            else ""
        )
        if coolq_edition != "":
            coolq_edition = coolq_edition[0].upper() + coolq_edition[1:]
        friend_list = json.loads(bot.friend_list)
        friend_num = (
            len(friend_list)
            if friend_list
            else "-1"
        )
        group_list = json.loads(bot.group_list)
        group_num = len(group_list) if group_list else -1
        bb["name"] = bot.name
        if bot.public:
            bb["user_id"] = bot.user_id
        else:
            mid = len(bot.user_id) // 2
            user_id = bot.user_id[: mid - 2] + "*" * 4 + bot.user_id[mid + 2:]
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
