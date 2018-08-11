from django.contrib import admin
from .models import *
# Register your models here.

class QQGroupAdmin(admin.ModelAdmin):
    list_display = ('group_id','welcome_msg')
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

admin.site.register(QQGroup,QQGroupAdmin)
admin.site.register(CustomReply,CustomReplyAdmin)
admin.site.register(ChatMessage,ChatMessageAdmin)
admin.site.register(BanMember,BanMemberAdmin)
admin.site.register(Revenge,RevengeAdmin)
admin.site.register(Quest,QuestAdmin)
admin.site.register(Boss,BossAdmin)
admin.site.register(Job,JobAdmin)
admin.site.register(DPSTile,DPSTileAdmin)