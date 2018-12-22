from django.db import models
import json
import time
# Create your models here.

class WeiboUser(models.Model):
	name = models.CharField(default="",blank=True,max_length=16,unique=True)
	uid = models.CharField(default="",max_length=16)
	containerid = models.CharField(default="",max_length=32)
	last_update_time = models.BigIntegerField(default=0)
	def __str__(self):
		return self.name

class QQGroup(models.Model):
	group_id = models.CharField(primary_key=True,max_length=16,unique=True)
	welcome_msg = models.TextField(default="",blank=True)
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
	subscription = models.ManyToManyField(WeiboUser, related_name="subscribed_by", blank=True)
	commands = models.TextField(default="{}")
	def __str__(self):
		return self.group_id

class WeiboTile(models.Model):
	itemid = models.CharField(default="",max_length=128,unique=True)
	owner = models.ForeignKey(WeiboUser, on_delete=models.CASCADE, related_name="tile")
	content = models.TextField(default="{}")
	crawled_time = models.BigIntegerField(default=0)
	pushed_group = models.ManyToManyField(QQGroup, related_name="pushed_weibo")
	def __str__(self):
		return self.itemid



class CustomReply(models.Model):
	group = models.ForeignKey(QQGroup,on_delete=models.CASCADE)
	key = models.TextField(default="",blank=True)
	value = models.TextField(default="",blank=True)

class ChatMessage(models.Model):
	group = models.ForeignKey(QQGroup,on_delete=models.CASCADE)
	message = models.TextField(default="",blank=True)
	timestamp = models.BigIntegerField(default=0)
	times = models.IntegerField(default=1)
	repeated = models.BooleanField(default=False)

class BanMember(models.Model):
	user_id = models.CharField(max_length=16)
	group = models.ForeignKey(QQGroup,on_delete=models.CASCADE)
	ban_time = models.IntegerField(default=0)
	vote_list = models.TextField(default="{}")
	timestamp = models.BigIntegerField(default=0)

class Revenge(models.Model):
	user_id = models.CharField(max_length=16)
	group = models.ForeignKey(QQGroup,on_delete=models.CASCADE)
	vote_list = models.TextField(default="{}")
	timestamp = models.BigIntegerField(default=0)
	ban_time = models.IntegerField(default=0)


class Quest(models.Model):
	quest_id = models.IntegerField(primary_key=True)
	name = models.CharField(default="",max_length=64,blank=True)
	cn_name = models.CharField(default="",max_length=64,blank=True)
	def __str__(self):
		return str(self.name)

class Boss(models.Model):
	boss_id = models.IntegerField(primary_key=True)
	quest = models.ForeignKey(Quest,on_delete=models.CASCADE)
	name = models.CharField(default="",max_length=64,blank=True)
	cn_name = models.CharField(default="",max_length=64,blank=True)
	nickname = models.TextField(default="{}")
	add_time = models.BigIntegerField(default=0)
	cn_add_time = models.BigIntegerField(default=0)
	parsed_days = models.IntegerField(default=0)
	def __str__(self):
		return str(self.name)

class Job(models.Model):
	name = models.CharField(default="",max_length=64,blank=True)
	cn_name = models.CharField(default="",max_length=64,blank=True)
	nickname = models.TextField(default="{}")
	def __str__(self):
		return str(self.name)


class Vote(models.Model):
	group = models.ForeignKey(QQGroup,on_delete=models.CASCADE)
	name = models.CharField(max_length=64)
	starttime = models.BigIntegerField(default=0)
	endtime = models.BigIntegerField(default=0)
	vote = models.TextField(default="{}")
	def __str__(self):
		return str(self.name)


class RandomScore(models.Model):
	user_id = models.CharField(max_length=16)
	group = models.ForeignKey(QQGroup,on_delete=models.CASCADE)
	max_random = models.IntegerField(default=0)
	min_random = models.IntegerField(default=1001)


class QQBot(models.Model):
	name = models.CharField(max_length=16)
	user_id = models.CharField(max_length=16,unique=True)
	owner_id = models.CharField(max_length=16)
	access_token = models.CharField(max_length=16,default="")
	auto_accept_friend = models.BooleanField(default=False)
	auto_accept_invite = models.BooleanField(default=False)
	tuling_token = models.CharField(max_length=32,default="",blank=True)
	saucenao_token = models.CharField(max_length=32,default="",blank=True)
	api_channel_name = models.CharField(max_length=32,default="",blank=True)
	event_channel_name = models.CharField(max_length=32,default="",blank=True)
	group_list = models.TextField(default="[]")
	plugin_status = models.TextField(default="{}")
	version_info = models.TextField(default="{}")
	event_time = models.BigIntegerField(default=0)
	api_time = models.BigIntegerField(default=0)
	long_query_interval = models.IntegerField(default=15)
	friend_list = models.TextField(default="{}")
	public = models.BooleanField(default=True)
	r18 = models.BooleanField(default=False)
	disconnections = models.TextField(default="[]")
	disconnect_time = models.BigIntegerField(default=0)
	command_stat = models.TextField(default="{}")
	share_banned = models.BooleanField(default=False)
	img_banned = models.BooleanField(default=False)
	def __str__(self):
		return self.name

class PlotQuest(models.Model):
	name = models.CharField(max_length=32,unique=True)
	version = models.CharField(max_length=64)
	area = models.CharField(max_length=16)
	category = models.CharField(max_length=32)
	sub_category = models.CharField(max_length=32)
	job = models.CharField(max_length=64)
	startnpc = models.CharField(max_length=64)
	endnpc = models.CharField(max_length=64)
	suf_quests = models.ManyToManyField("self",blank=True,symmetrical=False,related_name="pre_quests")
	endpoint = models.BooleanField(default=False)
	html = models.TextField(default="",blank=True)
	crawl_status = models.IntegerField(default=0)
	def __str__(self):
		return self.name

class Comment(models.Model):
	left_by = models.CharField(max_length=16)
	left_time = models.BigIntegerField(default=0)
	content = models.TextField(default="",blank=True)
	def __str__(self):
		return self.content[:10]

class Server(models.Model):
	name = models.CharField(max_length=16)
	areaId = models.IntegerField(default=1)
	groupId = models.IntegerField(default=25)
	alter_names = models.TextField(default="[]")

	def __str__(self):
		return self.name

class SorryGIF(models.Model):
	name = models.CharField(max_length=16)
	api_name = models.CharField(max_length=32)
	example = models.TextField(default="")

	def __str__(self):
		return self.name

class QQUser(models.Model):
	user_id = models.CharField(max_length=16,unique=True)
	bot_token = models.CharField(max_length=16)

	def __str__(self):
		return str(self.user_id)

class HsoAlterName(models.Model):
	name = models.CharField(max_length=32,unique=True,default="")
	key = models.CharField(max_length=64,default="")

	def __str__(self):
		return self.name

class Weather(models.Model):
	id = models.IntegerField(primary_key=True)
	name = models.CharField(max_length=32,default="")

	def __str__(self):
		return self.name

class WeatherRate(models.Model):
	id = models.IntegerField(primary_key=True)
	rate = models.TextField(default="[]")

class Territory(models.Model):
	name = models.CharField(max_length=32,default="")
	nickname = models.TextField(default="[]")
	weather_rate = models.ForeignKey(WeatherRate,blank=True,null=True,on_delete=models.CASCADE)

	def __str__(self):
		return self.name
