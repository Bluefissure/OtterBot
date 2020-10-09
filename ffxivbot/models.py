from django.db import models
from django.contrib.auth.models import User
from datetime import datetime
from pytz import timezone
import requests
import os
import json
import time

# Create your models here.


class WeiboUser(models.Model):
    name = models.CharField(default="", blank=True, max_length=16, unique=True)
    uid = models.CharField(default="", max_length=16)
    containerid = models.CharField(default="", max_length=32)
    last_update_time = models.BigIntegerField(default=0)

    def __str__(self):
        return self.name


class LiveUser(models.Model):
    room_id = models.CharField(max_length=16, default="", blank=True)
    name = models.CharField(max_length=64)
    platform = models.CharField(max_length=16, default="bilibili")
    info = models.TextField(default="{}")
    status = models.CharField(max_length=32, default="default")
    last_update_time = models.BigIntegerField(default=0)

    def __str__(self):
        return "{}#{}:{}".format(self.platform, self.room_id, self.name)

    def get_share(self, mode="json"):
        jinfo = json.loads(self.info)
        if self.platform == "bilibili":
            res_data = {
                "url": "https://live.bilibili.com/{}".format(self.room_id),
                "title": jinfo.get("title", "{}的直播".format(self.name)),
                "content": "{}开始在{}直播啦~".format(self.name, self.platform),
                "image": jinfo.get("image", ""),
            }
        elif self.platform == "douyu":
            content = "{}开始在{}直播啦~".format(self.name, self.platform)
            res_data = {
                "url": "https://www.douyu.com/{}".format(self.room_id),
                "title": jinfo.get("title", "{}的直播".format(self.name)),
                "content": content,
                "image": jinfo.get("image", ""),
            }
        else:
            res_data = {
                "url": "https://jq.qq.com/?_wv=1027&k=5L3hY4w",
                "title": "NotImplementedPlatform",
                "content": "欢迎加群660557003反映问题",
                "image": "https://xn--v9x.net/static/dist/img/tata.jpg",
            }
        if mode == "text":
            res_data = "[[CQ:share,url={},title={},content={},image={}]]".format(
                res_data["url"],
                res_data["title"],
                res_data["content"],
                res_data["image"],
            )
        return res_data

    def is_live(self):
        jinfo = json.loads(self.info)
        return jinfo.get("status", "offline").lower() == "live"


class Server(models.Model):
    name = models.CharField(max_length=16)
    areaId = models.IntegerField(default=1)
    groupId = models.IntegerField(default=25)
    alter_names = models.TextField(default="[]")
    worldId = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class QQGroup(models.Model):
    group_id = models.CharField(primary_key=True, max_length=64, unique=True)
    welcome_msg = models.TextField(default="", blank=True)
    bots = models.TextField(default="[]")
    repeat_ban = models.IntegerField(default=-1)
    repeat_length = models.IntegerField(default=-1)
    repeat_prob = models.IntegerField(default=0)
    left_reply_cnt = models.IntegerField(default=100)
    ban_cnt = models.IntegerField(default=-1)
    ban_till = models.BigIntegerField(default=0)
    last_reply_time = models.BigIntegerField(default=0)
    member_list = models.TextField(default="[]")
    registered = models.BooleanField(default=False)
    subscription = models.ManyToManyField(
        WeiboUser, related_name="subscribed_by", blank=True
    )
    live_subscription = models.ManyToManyField(
        LiveUser, related_name="subscribed_by", blank=True
    )
    pushed_live = models.ManyToManyField(
        LiveUser, related_name="pushed_group", blank=True
    )
    commands = models.TextField(default="{}")
    api = models.BooleanField(default=False)
    server = models.ForeignKey(
        Server, on_delete=models.DO_NOTHING, blank=True, null=True
    )

    def __str__(self):
        return self.group_id


class WeiboTile(models.Model):
    itemid = models.CharField(default="", max_length=128, unique=True)
    owner = models.ForeignKey(WeiboUser, on_delete=models.CASCADE, related_name="tile")
    content = models.TextField(default="{}")
    crawled_time = models.BigIntegerField(default=0)
    pushed_group = models.ManyToManyField(QQGroup, related_name="pushed_weibo")

    def __str__(self):
        return self.itemid


class CustomReply(models.Model):
    group = models.ForeignKey(QQGroup, on_delete=models.CASCADE)
    key = models.CharField(default="", max_length=64, blank=True)
    value = models.TextField(default="", blank=True)

    class Meta:
        indexes = [models.Index(fields=["group", "key"])]


class ChatMessage(models.Model):
    group = models.ForeignKey(QQGroup, on_delete=models.CASCADE)
    message = models.TextField(default="", blank=True)
    message_hash = models.CharField(default="", max_length=32, blank=True)
    timestamp = models.BigIntegerField(default=0)
    times = models.IntegerField(default=1)
    repeated = models.BooleanField(default=False)

    class Meta:
        indexes = [models.Index(fields=["group", "message_hash"])]


class BanMember(models.Model):
    user_id = models.CharField(max_length=64)
    group = models.ForeignKey(QQGroup, on_delete=models.CASCADE)
    ban_time = models.IntegerField(default=0)
    vote_list = models.TextField(default="{}")
    timestamp = models.BigIntegerField(default=0)


class Revenge(models.Model):
    user_id = models.CharField(max_length=64)
    group = models.ForeignKey(QQGroup, on_delete=models.CASCADE)
    vote_list = models.TextField(default="{}")
    timestamp = models.BigIntegerField(default=0)
    ban_time = models.IntegerField(default=0)


class Quest(models.Model):
    quest_id = models.IntegerField(primary_key=True)
    name = models.CharField(default="", max_length=64, blank=True)
    cn_name = models.CharField(default="", max_length=64, blank=True)

    def __str__(self):
        return str(self.name)


class Boss(models.Model):
    boss_id = models.IntegerField(primary_key=True)
    quest = models.ForeignKey(Quest, on_delete=models.CASCADE)
    name = models.CharField(default="", max_length=64, blank=True)
    cn_name = models.CharField(default="", max_length=64, blank=True)
    nickname = models.TextField(default="{}")
    add_time = models.BigIntegerField(default=0)
    cn_add_time = models.BigIntegerField(default=0)
    cn_offset = models.IntegerField(default=0)
    parsed_days = models.IntegerField(default=0)
    frozen = models.BooleanField(default=False)
    patch = models.IntegerField(default=0)
    savage = models.IntegerField(default=100)  # 100 for normal; 101 for savage
    global_server = models.IntegerField(
        default=3
    )  # 3 for boss after 5.0, 1 for boss before 5.0
    cn_server = models.IntegerField(
        default=5
    )  # 5 for boss after 5.0, 3 for boss before 5.0

    def __str__(self):
        return str(self.name)


class Job(models.Model):
    name = models.CharField(default="", max_length=64, blank=True)
    cn_name = models.CharField(default="", max_length=64, blank=True)
    nickname = models.TextField(default="{}")

    def __str__(self):
        return str(self.name)


class Vote(models.Model):
    group = models.ForeignKey(QQGroup, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    starttime = models.BigIntegerField(default=0)
    endtime = models.BigIntegerField(default=0)
    vote = models.TextField(default="{}")

    def __str__(self):
        return str(self.name)


class QQBot(models.Model):
    name = models.CharField(max_length=16)
    user_id = models.CharField(max_length=64, unique=True)
    wechat_id = models.CharField(max_length=64, default="", blank=True)
    owner_id = models.CharField(max_length=16)
    access_token = models.CharField(max_length=16, default="")
    auto_accept_friend = models.BooleanField(default=False)
    auto_accept_invite = models.BooleanField(default=False)
    tuling_token = models.CharField(max_length=32, default="", blank=True)
    saucenao_token = models.CharField(max_length=32, default="", blank=True)
    api_channel_name = models.CharField(max_length=128, default="", blank=True)
    event_channel_name = models.CharField(max_length=128, default="", blank=True)
    api_post_url = models.CharField(max_length=128, default="", blank=True)
    iotqq_url = models.CharField(max_length=128, default="", blank=True)
    iotqq_auth = models.CharField(max_length=32, default="", blank=True)
    group_list = models.TextField(default="[]")
    plugin_status = models.TextField(default="{}")
    version_info = models.TextField(default="{}")
    event_time = models.BigIntegerField(default=0)
    api_time = models.BigIntegerField(default=0)
    long_query_interval = models.IntegerField(default=15)
    friend_list = models.TextField(default="{}")
    public = models.BooleanField(default=True)
    r18 = models.BooleanField(default=False)
    api = models.BooleanField(default=True)
    disconnections = models.TextField(default="[]")
    disconnect_time = models.BigIntegerField(default=0)
    command_stat = models.TextField(default="{}")
    share_banned = models.BooleanField(default=False)
    img_banned = models.BooleanField(default=False)

    def __str__(self):
        return self.name


class PlotQuest(models.Model):
    name = models.CharField(max_length=128)
    tooltip_url = models.TextField(default="", blank=True)
    tooltip_html = models.TextField(default="", blank=True)
    pre_quests = models.ManyToManyField(
        "self", blank=True, symmetrical=False, related_name="suf_quests"
    )
    language_names = models.TextField(default="{}", blank=True)
    endpoint = models.BooleanField(default=False)
    endpoint_desc = models.CharField(max_length=64, default="", blank=True)
    quest_type = models.IntegerField(
        default=0
    )  # 0:nothing 3:main-scenario 8:special 1,10:other

    def __str__(self):
        return self.name

    def is_main_scenario(self):
        return self.quest_type == 3

    def is_special(self):
        return self.quest_type == 8


class Comment(models.Model):
    left_by = models.CharField(max_length=16)
    left_group = models.CharField(max_length=16, default="")
    left_time = models.BigIntegerField(default=0)
    bot_id = models.CharField(max_length=16, default="")
    content = models.TextField(default="", blank=True)
    reply = models.TextField(default="", blank=True)

    def __str__(self):
        return self.content[:10]


class SorryGIF(models.Model):
    name = models.CharField(max_length=16)
    api_name = models.CharField(max_length=32)
    example = models.TextField(default="")

    def __str__(self):
        return self.name


class QQUser(models.Model):
    dbuser = models.OneToOneField(
        User, on_delete=models.DO_NOTHING, blank=True, null=True, related_name="qquser"
    )
    user_id = models.CharField(max_length=64, unique=True)
    bot_token = models.CharField(max_length=16, blank=True)
    able_to_upload_image = models.BooleanField(default=True)
    last_api_time = models.BigIntegerField(default=0)
    last_chat_time = models.BigIntegerField(default=0)
    api_interval = models.IntegerField(default=5)
    ban_till = models.BigIntegerField(default=0)
    ban_share_till = models.BigIntegerField(default=0)
    sent_weibo = models.TextField(default="[]")
    ifttt_token = models.CharField(default="", max_length=128, blank=True)
    nickname = models.CharField(default="", max_length=64, blank=True)
    avatar_url = models.CharField(default="", max_length=256, blank=True)
    open_id = models.CharField(default="", max_length=128, blank=True)
    vcode = models.CharField(default="", max_length=16, blank=True)
    vcode_time = models.BigIntegerField(default=0)
    timezone = models.CharField(default="Asia/Shanghai", max_length=32)
    server = models.ForeignKey(
        Server, on_delete=models.DO_NOTHING, blank=True, null=True
    )

    def __str__(self):
        return str(self.user_id)


class HsoAlterName(models.Model):
    name = models.CharField(max_length=32, unique=True, default="")
    key = models.CharField(max_length=64, default="")

    def __str__(self):
        return self.name


class Weather(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=32, default="")

    def __str__(self):
        return self.name


class WeatherRate(models.Model):
    id = models.IntegerField(primary_key=True)
    rate = models.TextField(default="[]")


class Territory(models.Model):
    name = models.CharField(max_length=32, default="")
    nickname = models.TextField(default="[]")
    weather_rate = models.ForeignKey(
        WeatherRate, blank=True, null=True, on_delete=models.CASCADE
    )
    mapid = models.IntegerField(default=0)

    def __str__(self):
        return self.name


class Image(models.Model):
    domain = models.CharField(max_length=128, default="https://i.loli.net")
    url = models.CharField(max_length=128, default="")
    key = models.CharField(max_length=16, default="")
    name = models.CharField(max_length=32, default="")
    path = models.CharField(max_length=64, default="", unique=True)
    img_hash = models.CharField(max_length=32, default="")
    timestamp = models.IntegerField(default=0)
    add_by = models.ForeignKey(
        QQUser, on_delete=models.CASCADE, related_name="upload_images"
    )

    def __str__(self):
        return self.name


class Lottery(models.Model):
    name = models.CharField(max_length=32, default="")
    description = models.TextField(default="", blank=True, null=True)
    group = models.ForeignKey(
        QQGroup, on_delete=models.CASCADE, related_name="lotteries"
    )
    host_user = models.CharField(max_length=16, default="")
    participate_user = models.TextField(default="[]")
    prize = models.TextField(default="[]")
    random_res = models.TextField(default="{}")
    begin_time = models.BigIntegerField(default=0)
    end_time = models.BigIntegerField(default=0)
    uuid = models.CharField(max_length=36, unique=True)  # uuid.uuid4()
    public = models.BooleanField(default=False)
    max_participate = models.IntegerField(default=-1)
    mode = models.IntegerField(default=1)  # 0: system random shuffle 1: random.org

    def __str__(self):
        return self.name

    def winner_info(self):
        res_json = json.loads(self.random_res)
        msg = ""
        try:
            random_list = res_json["result"]["random"]["data"]
        except KeyError:
            return "KeyError"
        else:
            member_score_list = []
            members = json.loads(self.participate_user)
            prizes = json.loads(self.prize)
            for member, score in zip(members, random_list):
                member_score_list.append((member, score))
            member_score_list.sort(key=lambda x: x[1], reverse=True)
            for member, prize in zip(member_score_list, prizes):
                msg += "[CQ:at,qq={}] --- {}\n".format(member[0], prize)
        return msg

    def prize_info(self):
        prizes = json.loads(self.prize)
        prize_dict = {}
        for p in prizes:
            if p not in prize_dict.keys():
                prize_dict[p] = 1
            else:
                prize_dict[p] += 1
        return ", ".join(
            ["{}*{}".format(item[0], item[1]) for item in prize_dict.items()]
        )

    def info(self, **kwargs):
        msg = "抽奖 #{}: {} 的信息如下：".format(self.id, self.name)
        TIMEFORMAT = kwargs.get("TIMEFORMAT", None)
        import time

        msg += "\n开始时间：{}".format(
            time.strftime(TIMEFORMAT, time.localtime(self.begin_time))
            if TIMEFORMAT
            else self.begin_time
        )
        if self.end_time > 0:
            msg += "\n结束时间：{}".format(
                time.strftime(TIMEFORMAT, time.localtime(self.end_time))
                if TIMEFORMAT
                else self.end_time
            )
        prizes = self.prize_info()
        msg += "\n奖品：{}".format(prizes)
        mems = " ".join(
            ["[CQ:at,qq={}]".format(qq) for qq in json.loads(self.participate_user)]
        )
        msg += "\n参与人：{}".format(mems)
        if time.time() > self.end_time and self.end_time > 0:
            msg += "\n获奖者：{}".format(self.winner_info())
        return msg


class ContentFinderItem(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=64, default="")
    nickname = models.TextField(default="{}")
    guide = models.TextField(default="")

    def __str__(self):
        return self.name


class CommandLog(models.Model):
    time = models.BigIntegerField(default=0)
    command = models.CharField(max_length=32)
    message = models.TextField(default="")
    bot_id = models.CharField(max_length=16)
    user_id = models.CharField(max_length=64)
    group_id = models.CharField(max_length=64)


class HuntGroup(models.Model):
    name = models.CharField(default="", max_length=64)
    group = models.ForeignKey(
        QQGroup, on_delete=models.CASCADE, related_name="hunt_group"
    )
    server = models.ForeignKey(
        Server, on_delete=models.CASCADE, related_name="hunt_group"
    )
    moderator = models.ManyToManyField(
        QQUser, related_name="managed_hunt_group", blank=True
    )
    servermark = models.CharField(default="", max_length=16, blank=True, null=True)
    remark = models.CharField(default="", max_length=64, blank=True, null=True)
    public = models.BooleanField(default=False)

    def __str__(self):
        return self.name if self.name else "{}-{}".format(self.group, self.server)


class Monster(models.Model):
    name = models.CharField(default="", blank=True, max_length=32, unique=True)
    cn_name = models.CharField(default="", blank=True, max_length=32)
    territory = models.ForeignKey(
        Territory, on_delete=models.CASCADE, related_name="hunt_monster"
    )
    rank = models.CharField(default="A", max_length=5)  # enum: "A", "B", "S", "Fate"
    spawn_cooldown = models.IntegerField(default=0)
    first_spawn_cooldown = models.IntegerField(default=0)
    pop_cooldown = models.IntegerField(default=0)
    first_pop_cooldown = models.IntegerField(default=0)
    info = models.CharField(default="", max_length=128)
    status = models.TextField(default="{}")

    def spawn_cd_hour(self):
        return self.spawn_cooldown // 3600

    def pop_cd_hour(self):
        return self.pop_cooldown // 3600

    def __str__(self):
        return self.cn_name if self.cn_name else self.name


class HuntLog(models.Model):
    monster = models.ForeignKey(
        Monster,
        on_delete=models.CASCADE,
        related_name="hunt_log",
        blank=True,
        null=True,
    )
    hunt_group = models.ForeignKey(
        HuntGroup, on_delete=models.CASCADE, related_name="hunt_log"
    )
    server = models.ForeignKey(
        Server, on_delete=models.CASCADE, related_name="hunt_log"
    )
    log_type = models.CharField(default="", max_length=16)
    time = models.BigIntegerField(default=0)

    def __str__(self):
        return "{}-{}".format(self.server, self.monster)

    def get_info(self):
        return "HuntLog#{}: {}-{} {}".format(
            self.id, self.server, self.monster, self.log_type
        )


## class TelegramChannel(models.Model):
##     name = models.CharField(default="", max_length=64)
##     group = models.ManyToManyField(QQGroup, null=True, blank=True, related_name="tele_channel")
##     last_push_time = models.BigIntegerField(default=0)
##
##     def __str__(self):
##         return self.name


class IFTTTChannel(models.Model):
    name = models.CharField(default="", max_length=32)
    group = models.ForeignKey(
        QQGroup,
        null=True,
        blank=True,
        related_name="ifttt_channel",
        on_delete=models.CASCADE,
    )
    members = models.ManyToManyField(QQUser, blank=True)
    last_push_time = models.BigIntegerField(default=0)
    callback_link = models.CharField(default="", max_length=256, blank=True, null=True)

    def __str__(self):
        return self.name


class TreasureMap(models.Model):
    territory = models.ForeignKey(
        Territory, blank=True, null=True, on_delete=models.CASCADE
    )
    position = models.TextField(default="[0, 0]")
    rank = models.CharField(max_length=8, default="")
    number = models.IntegerField(default=0)
    uri = models.TextField(default="")

    def __str__(self):
        return "{}#{}".format(self.territory, self.number)


class Screen(models.Model):
    name = models.CharField(default="", max_length=64, blank=True)
    nickname = models.TextField(default="{}")
    classname = models.CharField(default="", max_length=64, blank=True)

    def __str__(self):
        return str(self.name)


class LuckData(models.Model):
    number = models.IntegerField(default=0)
    text = models.TextField(default="")
    img_url = models.CharField(max_length=128, default="")

    def __str__(self):
        return str(self.number)


class TomonBot(models.Model):
    qqbot = models.ForeignKey(
        QQBot, related_name="tomon_bot", on_delete=models.CASCADE, blank=True, null=True
    )
    username = models.CharField(max_length=32)
    password = models.CharField(max_length=32)
    token = models.CharField(max_length=256, blank=True)
    last_heartbeat = models.BigIntegerField(default=0)
    heartbeat_interval = models.BigIntegerField(default=0)
    bot = models.BooleanField(default=False)

    def auth(self, api_base="https://beta.tomon.co/api/v1"):
        if self.bot:
            return
        auth_url = os.path.join(api_base, "auth/login")
        payload = {"full_name": self.username, "password": self.password}
        r = requests.post(auth_url, data=payload)
        if r.status_code == 200:
            res = r.json()
            self.token = res["token"]
            self.save()
        else:
            print("Error Response: {}\n{}".format(r.status_code, r.json()))
