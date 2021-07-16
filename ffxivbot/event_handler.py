import time
from datetime import timedelta
import json
from .models import QQGroup, QQBot, QQUser
from .api_caller import ApiCaller
from handlers.QQUtils import text2img
import handlers
import traceback


class EventHandler(object):
    def __init__(self, bot, api_caller=None):
        self.bot = bot
        self.api_caller = api_caller or ApiCaller(bot)

    def on_message(self, receive, **kwargs):
        bot = self.bot
        config = kwargs.get("config")
        already_reply = False
        user_id = receive["user_id"]
        if QQBot.objects.filter(user_id=user_id).exists():
            # print("{} reply from another bot:{}".format(receive["self_id"], user_id))
            return
        (user, created) = QQUser.objects.get_or_create(user_id=user_id)
        if 0 < time.time() < user.ban_till:
            delta = timedelta(seconds= user.ban_till - time.time())
            raise Exception("User {} get banned for {}".format(user_id, delta))

        # replace alter commands
        for (alter_command, command) in handlers.alter_commands.items():
            if receive["message"].startswith(alter_command):
                receive["message"] = receive["message"].replace(
                    alter_command, command, 1
                )
                break

        group_id = None
        group = None
        group_created = False
        discuss_id = None
        if receive["message"].startswith("\\"):
            receive["message"] = receive["message"].replace("\\", "/", 1)
        if receive["message_type"] == "discuss":
            discuss_id = receive["discuss_id"]

        # Handle QQGroupCommand_*
        if receive["message_type"] == "group":
            group_id = receive["group_id"]
            # get sender's user_info
            user_info = receive.get("sender")
            (group, group_created) = QQGroup.objects.get_or_create(group_id=group_id)
            # self-ban in group
            if int(time.time()) < group.ban_till:
                raise Exception("{} banned by group:{}".format(self_id, group_id))
            group_commands = json.loads(group.commands)
            group_bots = json.loads(group.bots)

            try:
                member_list = json.loads(group.member_list)
                if group_created or not member_list:
                    self.api_caller.update_group_member_list(
                        group_id,
                        post_type=receive.get("reply_api_type", "websocket"),
                        channel_id=receive.get("channel_id", ""),
                    )
            except json.decoder.JSONDecodeError:
                member_list = []

            if receive["message"].startswith("/group_help"):
                msg = (
                    "" if member_list else "本群成员信息获取失败，请尝试重启酷Q并使用/update_group刷新群成员信息\n"
                )
                for (k, v) in handlers.group_commands.items():
                    command_enable = True
                    if group and group_commands:
                        command_enable = group_commands.get(k, "enable") == "enable"
                    if command_enable:
                        msg += "{}: {}\n".format(k, v)
                msg = text2img(msg)
                msg += "具体介绍详见Wiki使用手册: \n{}\n".format(
                    "https://github.com/Bluefissure/OtterBot/wiki"
                )
                msg = msg.strip()
                self.api_caller.send_message(
                    receive["message_type"],
                    discuss_id or group_id or user_id,
                    msg,
                    post_type=receive.get("reply_api_type", "websocket"),
                    chatId=receive.get("chatId", ""),
                    channel_id=receive.get("channel_id", ""),
                    nonce=receive.get("nonce", ""),
                )
            else:
                if receive["message"].startswith("/update_group"):
                    self.api_caller.update_group_member_list(
                        group_id,
                        post_type=receive.get("reply_api_type", "websocket"),
                        channel_id=receive.get("channel_id", ""),
                    )
                if not user_info or ("role" not in user_info):
                    user_info = None
                if member_list and not user_info:
                    for item in member_list:
                        if str(item["user_id"]) == str(user_id):
                            user_info = item
                            break
                if not user_info:
                    if receive.get("reply_api_type", "websocket") == "wechat":
                        user_info = {
                            "user_id": receive["user_id"],
                            "nickname": receive["data"]["contactName"],
                            "role": "member",
                        }
                        if receive["user_id"] not in list(
                            map(lambda x: x["user_id"], member_list)
                        ):
                            member_list.append(user_info)
                            group.member_list = json.dumps(member_list)
                            group.save(update_fields=["member_list"])
                    else:
                        raise Exception(
                            "No user info for user_id:{} in group:{}".format(
                                user_id, group_id
                            )
                        )
                group_command_keys = sorted(
                    handlers.group_commands.keys(), key=lambda x: -len(x)
                )
                for command_key in group_command_keys:
                    if receive["message"].startswith(command_key):
                        if receive["message_type"] == "group" and group_commands:
                            if group_commands.get(command_key, "enable") == "disable":
                                continue
                        if not group.registered and command_key != "/group":
                            msg = "本群%s未在数据库注册，请群主使用/register_group命令注册" % (group_id)
                            self.api_caller.send_message(
                                "group",
                                group_id,
                                msg,
                                post_type=receive.get("reply_api_type", "websocket"),
                                chatId=receive.get("chatId", ""),
                                channel_id=receive.get("channel_id", ""),
                                nonce=receive.get("nonce", ""),
                            )
                            break
                        else:
                            handle_method = getattr(
                                handlers,
                                "QQGroupCommand_{}".format(
                                    command_key.replace("/", "", 1)
                                ),
                            )
                            action_list = handle_method(
                                receive=receive,
                                global_config=config,
                                bot=bot,
                                user_info=user_info,
                                member_list=member_list,
                                group=group,
                                commands=handlers.commands,
                                group_commands=handlers.group_commands,
                                alter_commands=handlers.alter_commands,
                            )
                            for action in action_list:
                                self.api_caller.call_api(
                                    action["action"],
                                    action["params"],
                                    echo=action["echo"],
                                    post_type=receive.get(
                                        "reply_api_type", "websocket"
                                    ),
                                    chatId=receive.get("chatId", ""),
                                    channel_id=receive.get("channel_id", ""),
                                )
                                already_reply = True
                            if already_reply:
                                break
        # Handle /help
        if receive["message"].startswith("/help"):
            msg = ""
            for (k, v) in handlers.commands.items():
                command_enable = True  # always True for private
                if group and group_commands:
                    command_enable = (
                        group_commands.get(k, "enable") == "enable"
                    )  # hide if disabled in group
                if command_enable:
                    msg += "{}: {}\n".format(k, v)
            msg = text2img(msg)
            msg += "具体介绍详见Wiki使用手册: \n{}\n".format(
                "https://github.com/Bluefissure/OtterBot/wiki"
            )
            msg = msg.strip()
            self.api_caller.send_message(
                receive["message_type"],
                group_id or user_id,
                msg,
                post_type=receive.get("reply_api_type", "websocket"),
                chatId=receive.get("chatId", ""),
                channel_id=receive.get("channel_id", ""),
                nonce=receive.get("nonce", ""),
            )
        # Handle /ping
        if receive["message"].startswith("/ping"):
            time_receive = receive["time"]
            if time_receive > 3000000000:
                time_from_receive = time_receive / 1000
            msg = ""
            if "detail" in receive["message"]:
                msg += "[CQ:at,qq={}]\nclient->server: {:.2f}s\nserver->rabbitmq: {:.2f}s\nhandle init: {:.2f}s".format(
                    receive["user_id"],
                    receive["consumer_time"] - time_receive,
                    receive["pika_time"] - receive["consumer_time"],
                    time.time() - receive["pika_time"],
                )
            else:
                msg += "[CQ:at,qq={}] {:.2f}s".format(
                    receive["user_id"], time.time() - time_receive
                )
            msg = msg.strip()
            # print(("{} calling command: {}".format(user_id, "/ping")))
            self.api_caller.send_message(
                receive["message_type"],
                discuss_id or group_id or user_id,
                msg,
                post_type=receive.get("reply_api_type", "websocket"),
                chatId=receive.get("chatId", ""),
                channel_id=receive.get("channel_id", ""),
                nonce=receive.get("nonce", ""),
            )
        # Handle QQCommand_*
        command_keys = sorted(handlers.commands.keys(), key=lambda x: -len(x))
        for command_key in command_keys:
            if receive["message"].startswith(command_key):
                if receive["message_type"] == "group":
                    if (
                        group_commands
                        and group_commands.get(command_key, "enable") == "disable"
                    ):
                        continue
                    if group_bots and str(receive["self_id"]) not in group_bots:
                        continue
                handle_method = getattr(
                    handlers, "QQCommand_{}".format(command_key.replace("/", "", 1)),
                )
                action_list = handle_method(
                    receive=receive, global_config=config, bot=bot
                )
                for action in action_list:
                    self.api_caller.call_api(
                        action["action"],
                        action["params"],
                        echo=action["echo"],
                        post_type=receive.get("reply_api_type", "websocket"),
                        chatId=receive.get("chatId", ""),
                        channel_id=receive.get("channel_id", ""),
                        nonce=receive.get("nonce", ""),
                    )
                    already_reply = True
                break

        # Handle group chat
        if receive["message_type"] == "group":
            if not already_reply:  # don't record already replied command
                action_list = handlers.QQGroupChat(
                    receive=receive,
                    global_config=config,
                    bot=bot,
                    user_info=user_info,
                    member_list=member_list,
                    group=group,
                    commands=handlers.commands,
                    alter_commands=handlers.alter_commands,
                )
                for action in action_list:
                    self.api_caller.call_api(
                        action["action"],
                        action["params"],
                        echo=action["echo"],
                        post_type=receive.get("reply_api_type", "websocket"),
                        chatId=receive.get("chatId", ""),
                        channel_id=receive.get("channel_id", ""),
                        nonce=receive.get("nonce", ""),
                    )

    def on_request(self, receive, **kwargs):
        print("on_request:{}".format(json.dumps(receive)))
        bot = self.bot
        config = kwargs.get("config")
        config_group_id = config["CONFIG_GROUP_ID"]
        if receive["request_type"] == "friend":  # Add Friend
            qq = receive["user_id"]
            flag = receive["flag"]
            if bot.auto_accept_friend:
                reply_data = {"flag": flag, "approve": True}
                print(
                    "calling set_friend_add_request:{}".format(json.dumps(reply_data))
                )
                self.api_caller.call_api(
                    "set_friend_add_request",
                    reply_data,
                    post_type=receive.get("reply_api_type", "websocket"),
                    channel_id=receive.get("channel_id", ""),
                )
        if receive["request_type"] == "group" and receive["sub_type"] == "invite":
            flag = receive["flag"]
            if bot.auto_accept_invite or str(receive["user_id"]) == bot.owner_id:
                reply_data = {
                    "flag": flag,
                    "sub_type": "invite",
                    "approve": True,
                }
                print("calling set_group_add_request:{}".format(json.dumps(reply_data)))
                self.api_caller.call_api(
                    "set_group_add_request",
                    reply_data,
                    post_type=receive.get("reply_api_type", "websocket"),
                )
        if (
            receive["request_type"] == "group"
            and receive["sub_type"] == "add"
            and str(receive["group_id"]) == config_group_id
        ):
            flag = receive["flag"]
            user_id = receive["user_id"]
            qs = QQBot.objects.filter(owner_id=user_id)
            if qs.count() > 0:
                reply_data = {"flag": flag, "sub_type": "add", "approve": True}
                print("calling set_group_add_request:{}".format(json.dumps(reply_data)))
                self.api_caller.call_api(
                    "set_group_add_request",
                    reply_data,
                    post_type=receive.get("reply_api_type", "websocket"),
                    channel_id=receive.get("channel_id", ""),
                )
                time.sleep(1)
                reply_data = {
                    "group_id": config_group_id,
                    "user_id": user_id,
                    "special_title": "饲养员",
                }
                self.api_caller.call_api(
                    "set_group_special_title",
                    reply_data,
                    post_type=receive.get("reply_api_type", "websocket"),
                    channel_id=receive.get("channel_id", ""),
                )

    def on_notice(self, receive, **kwargs):
        # print("on_notice:{}".format(json.dumps(receive)))
        bot = self.bot
        if receive.get("notice_type") == "group_increase" or (
            receive.get("notice_type") == "group"
            and receive.get("sub_type") == "increase"
        ):
            group_id = receive["group_id"]
            user_id = receive["user_id"]
            try:
                group = QQGroup.objects.get(group_id=group_id)
                welcome_msg = group.welcome_msg.strip()
                if welcome_msg:
                    msg = "[CQ:at,qq=%s]" % (user_id) + welcome_msg
                    # print("calling send_message:{}".format(msg))
                    self.api_caller.send_message(
                        "group",
                        group_id,
                        msg,
                        post_type=receive.get("reply_api_type", "websocket"),
                        chatId=receive.get("chatId", ""),
                        channel_id=receive.get("channel_id", ""),
                        nonce=receive.get("nonce", ""),
                    )
            except Exception as e:
                traceback.print_exc()

        if receive.get("notice_type") == "group_admin" or (
            receive.get("notice_type") == "group" and receive.get("sub_type") == "admin"
        ):
            self.api_caller.update_group_member_list(
                receive["group_id"],
                post_type=receive.get("reply_api_type", "websocket"),
                channel_id=receive.get("channel_id", ""),
            )
