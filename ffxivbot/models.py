from django.db import models
import json
import time
# Create your models here.
class QQGroup(models.Model):
	group_id = models.CharField(primary_key=True,max_length=16)
	welcome_msg = models.TextField(default="",blank=True)
	repeat_ban = models.IntegerField(default=-1)
	repeat_length = models.IntegerField(default=-1)
	repeat_prob = models.IntegerField(default=0)
	left_reply_cnt = models.IntegerField(default=100)
	ban_cnt = models.IntegerField(default=-1)
	ban_till = models.BigIntegerField(default=0)
	last_reply_time = models.BigIntegerField(default=0)
	member_list = models.TextField(default="[]")
	registered = models.BooleanField(default=False)

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

class DPSTile(models.Model):
	boss = models.ForeignKey(Boss,on_delete=models.CASCADE)
	job = models.ForeignKey(Job,on_delete=models.CASCADE)
	day = models.IntegerField(default=0)
	attack = models.TextField(default="{}")
	class Meta:
		unique_together = ('boss', 'job', 'day',)
	def __str__(self):
		return str("%s_%s_%s_%s"%(self.boss,self.job,self.day))


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
	last_reply_time = models.BigIntegerField(default=0)
	coolq_edition = models.CharField(max_length=4,default="air")
	api_data = models.TextField(default="[]")
	access_token = models.CharField(max_length=16,default="")
	auto_accept_friend = models.BooleanField(default=False)
	auto_accept_invite = models.BooleanField(default=False)
	tuling_token = models.CharField(max_length=32,default="",blank=True)
	api_last_time = models.BigIntegerField(default=0)
	event_last_time = models.BigIntegerField(default=0)
	api_channel_name = models.CharField(max_length=32,default="",blank=True)
	event_channel_name = models.CharField(max_length=32,default="",blank=True)
	def __str__(self):
		return self.name
	def clear_api_data(self):
		self.api_data = "[]"
		self.api_last_time = int(time.time())
		self.save()
	def send_ws_api(self,api,params,jdata=None):
		self.refresh_from_db()
		json_data = {
			"action": api,
			"params": params
		}
		if jdata:
			json_data = jdata
		print("%s api save:%s"%(self.user_id,json.dumps(json_data)))
		api_data = json.loads(self.api_data)
		if(type(api_data)==dict):
			api_data = [api_data]
		api_data.append(json_data)
		api_data = api_data[:10]
		self.api_data = json.dumps(api_data)
		self.event_last_time = int(time.time())
		self.save()
	def send_message(self,private_group,uid,message):
		message = "系统将于2018年8月13日 19:30:00开始维护，期间服务可能停止。"
		if(private_group=="group"):
			self.send_ws_api("send_group_msg",{"group_id":uid,"message":message})
		if(private_group=="private"):
			self.send_ws_api("send_private_msg",{"user_id":uid,"message":message})
	def update_group_member_list(self,group):
		jdata = {
			"action": "get_group_member_list",
			"params": {"group_id":group.group_id},
			"echo": "get_group_member_list:%s"%(group.group_id)
		}
		self.send_ws_api(None,None,jdata)
	def is_api_online(self):
		return time.time() - self.api_last_time <= 30
	def is_event_online(self):
		return time.time() - self.event_last_time <= 60
