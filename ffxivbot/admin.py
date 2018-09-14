from django.contrib import admin
from .models import *
# Register your models here.

class QQGroupAdmin(admin.ModelAdmin):
    list_display = ('group_id','welcome_msg','last_reply_time')
    search_fields = ['group_id']

class CustomReplyAdmin(admin.ModelAdmin):
    list_display = ('group','key','value')
    list_filter = ['group__group_id']
    search_fields = ['group__group_id','key','value']
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('group','message','timestamp','times','repeated')
    list_filter = ['group__group_id']
    search_fields = ['group__group_id']

class BanMemberAdmin(admin.ModelAdmin):
    list_display = ('user_id','group','vote_list')
    list_filter = ['group__group_id']
    search_fields = ['group__group_id','user_id']

class RevengeAdmin(admin.ModelAdmin):
    list_display = ('user_id','group','vote_list')
    list_filter = ['group__group_id']
    search_fields = ['group__group_id','user_id']

class QuestAdmin(admin.ModelAdmin):
    list_display = ('quest_id','name','cn_name')
    search_fields = ['name','cn_name']

class BossAdmin(admin.ModelAdmin):
    list_display = ('boss_id','name','cn_name')
    search_fields = ['name','cn_name']

class JobAdmin(admin.ModelAdmin):
    list_display = ('name','cn_name')
    search_fields = ['name','cn_name']

class DPSTileAdmin(admin.ModelAdmin):
    list_display = ('boss','job','day','attack')
    list_filter = ['boss','job','day']
    search_fields = ['boss','job','day']
class VoteAdmin(admin.ModelAdmin):
    list_display = ('name','starttime','endtime','group')
    list_filter = ['group']
    search_fields = ['name']
class RandomScoreAdmin(admin.ModelAdmin):
    list_display = ('user_id','group','min_random','max_random')
    list_filter = ['group']
    search_fields = ['user_id']
class QQBotAdmin(admin.ModelAdmin):
    list_display = ('name','user_id','access_token',"auto_accept_friend","auto_accept_invite")
class WeiboUserAdmin(admin.ModelAdmin):
    list_display = ('name','uid','containerid')
class WeiboTileAdmin(admin.ModelAdmin):
    list_display = ('itemid','owner','crawled_time')
    search_fields = ['itemid']
class PlotQuestAdmin(admin.ModelAdmin):
    list_display = ('name','area')
    list_filter = ['area','category','sub_category']
    search_fields = ['name']


admin.site.register(QQGroup,QQGroupAdmin)
admin.site.register(CustomReply,CustomReplyAdmin)
admin.site.register(ChatMessage,ChatMessageAdmin)
admin.site.register(BanMember,BanMemberAdmin)
admin.site.register(Revenge,RevengeAdmin)
admin.site.register(Quest,QuestAdmin)
admin.site.register(Boss,BossAdmin)
admin.site.register(Job,JobAdmin)
admin.site.register(DPSTile,DPSTileAdmin)
admin.site.register(Vote,VoteAdmin)
admin.site.register(RandomScore,RandomScoreAdmin)
admin.site.register(QQBot,QQBotAdmin)
admin.site.register(WeiboUser,WeiboUserAdmin)
admin.site.register(WeiboTile,WeiboTileAdmin)
admin.site.register(PlotQuest,PlotQuestAdmin)
