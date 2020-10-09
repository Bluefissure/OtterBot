from django.contrib import admin
from .models import *

# Register your models here.


class QQGroupAdmin(admin.ModelAdmin):
    list_display = ("group_id", "welcome_msg", "last_reply_time")
    search_fields = ["group_id"]


class CustomReplyAdmin(admin.ModelAdmin):
    list_display = ("group", "key", "value")
    list_filter = ["group__group_id"]
    search_fields = ["group__group_id", "key", "value"]


class ChatMessageAdmin(admin.ModelAdmin):
    list_display = (
        "group",
        "message",
        "timestamp",
        "message_hash",
        "times",
        "repeated",
    )
    list_filter = ["group__group_id"]
    search_fields = ["group__group_id", "message"]


class BanMemberAdmin(admin.ModelAdmin):
    list_display = ("user_id", "group", "vote_list")
    list_filter = ["group__group_id"]
    search_fields = ["group__group_id", "user_id"]


class RevengeAdmin(admin.ModelAdmin):
    list_display = ("user_id", "group", "vote_list")
    list_filter = ["group__group_id"]
    search_fields = ["group__group_id", "user_id"]


class QuestAdmin(admin.ModelAdmin):
    list_display = ("quest_id", "name", "cn_name")
    search_fields = ["name", "cn_name"]


class BossAdmin(admin.ModelAdmin):
    list_display = ("boss_id", "name", "cn_name")
    search_fields = ["name", "cn_name"]


class JobAdmin(admin.ModelAdmin):
    list_display = ("name", "cn_name")
    search_fields = ["name", "cn_name"]


class VoteAdmin(admin.ModelAdmin):
    list_display = ("name", "starttime", "endtime", "group")
    list_filter = ["group"]
    search_fields = ["name"]


class QQBotAdmin(admin.ModelAdmin):
    list_display = (
        "name",
        "user_id",
        "access_token",
        "auto_accept_friend",
        "auto_accept_invite",
        "owner_id",
    )
    search_fields = ["name", "user_id", "owner_id"]


class WeiboUserAdmin(admin.ModelAdmin):
    list_display = ("name", "uid", "containerid")


class WeiboTileAdmin(admin.ModelAdmin):
    list_display = ("itemid", "owner", "crawled_time")
    search_fields = ["itemid"]
    list_filter = ["owner"]


class PlotQuestAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "quest_type", "endpoint", "endpoint_desc"]
    search_fields = ["id", "name"]
    list_filter = ["quest_type"]


class CommentAdmin(admin.ModelAdmin):
    list_display = ("left_by", "content", "left_time")


class ServerAdmin(admin.ModelAdmin):
    list_display = ("name", "areaId", "groupId", "alter_names")


class SorryGIFAdmin(admin.ModelAdmin):
    list_display = ("name", "api_name")


class QQUserAdmin(admin.ModelAdmin):
    list_display = ("user_id", "bot_token")
    search_fields = ["user_id"]


class HsoAlterNameAdmin(admin.ModelAdmin):
    list_display = ("name", "key")


class WeatherAdmin(admin.ModelAdmin):
    list_display = ("id", "name")


class WeatherRateAdmin(admin.ModelAdmin):
    list_display = ["id"]


class TerritoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "mapid"]
    search_fields = ["name"]


class ImageAdmin(admin.ModelAdmin):
    list_display = ["name", "key", "add_by"]
    search_fields = ["name", "key", "add_by__user_id"]
    raw_id_fields = ["add_by"]


class LotteryAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "group"]
    search_fields = ["name", "group"]


class LiveUserAdmin(admin.ModelAdmin):
    list_display = ["name", "platform", "room_id"]
    search_fields = ["name", "platform", "room_id"]


class HuntGroupAdmin(admin.ModelAdmin):
    list_display = ["group", "server"]
    search_fields = ["group", "server"]
    raw_id_fields = ["group", "moderator"]


class MonsterAdmin(admin.ModelAdmin):
    list_display = [
        "name",
        "cn_name",
        "territory",
        "rank",
        "spawn_cd_hour",
        "pop_cd_hour",
    ]
    search_fields = ["name ", "cn_name"]
    list_filter = ["rank"]


class HuntLogAdmin(admin.ModelAdmin):
    list_display = ["monster", "hunt_group", "server", "log_type", "time"]
    search_fields = ["monster ", "hunt_group", "log_type"]
    list_filter = ["monster", "hunt_group", "server", "log_type"]
    raw_id_fields = ["hunt_group"]


class IFTTTChannelAdmin(admin.ModelAdmin):
    list_display = ["name", "group", "last_push_time"]
    search_fields = ["name ", "group"]
    raw_id_fields = ["members", "group"]


class TreasureMapAdmin(admin.ModelAdmin):
    list_display = ["territory", "number"]
    search_fields = ["territory"]
    list_filter = ["territory", "rank"]


class ScreenAdmin(admin.ModelAdmin):
    list_display = ("name", "id", "nickname", "classname")
    search_fields = ["name", "name"]


class LuckDataAdmin(admin.ModelAdmin):
    list_display = ["number"]


class TomonBotAdmin(admin.ModelAdmin):
    list_display = ["username", "qqbot"]


class CommandLogAdmin(admin.ModelAdmin):
    list_display = ["time", "command", "user_id", "bot_id", "group_id"]
    search_fields = ["command", "user_id", "bot_id", "group_id"]
    list_filter = ["command"]


admin.site.register(QQGroup, QQGroupAdmin)
admin.site.register(CustomReply, CustomReplyAdmin)
admin.site.register(ChatMessage, ChatMessageAdmin)
admin.site.register(BanMember, BanMemberAdmin)
admin.site.register(Revenge, RevengeAdmin)
admin.site.register(Quest, QuestAdmin)
admin.site.register(Boss, BossAdmin)
admin.site.register(Job, JobAdmin)
admin.site.register(Vote, VoteAdmin)
admin.site.register(QQBot, QQBotAdmin)
admin.site.register(WeiboUser, WeiboUserAdmin)
admin.site.register(WeiboTile, WeiboTileAdmin)
admin.site.register(PlotQuest, PlotQuestAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(Server, ServerAdmin)
admin.site.register(SorryGIF, SorryGIFAdmin)
admin.site.register(QQUser, QQUserAdmin)
admin.site.register(HsoAlterName, HsoAlterNameAdmin)
admin.site.register(Weather, WeatherAdmin)
admin.site.register(WeatherRate, WeatherRateAdmin)
admin.site.register(Territory, TerritoryAdmin)
admin.site.register(Image, ImageAdmin)
admin.site.register(Lottery, LotteryAdmin)
admin.site.register(LiveUser, LiveUserAdmin)
admin.site.register(HuntGroup, HuntGroupAdmin)
admin.site.register(Monster, MonsterAdmin)
admin.site.register(HuntLog, HuntLogAdmin)
admin.site.register(IFTTTChannel, IFTTTChannelAdmin)
admin.site.register(TreasureMap, TreasureMapAdmin)
admin.site.register(Screen, ScreenAdmin)
admin.site.register(LuckData, LuckDataAdmin)
admin.site.register(TomonBot, TomonBotAdmin)
admin.site.register(CommandLog, CommandLogAdmin)
