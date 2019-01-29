from .QQEventHandler import QQEventHandler
from .QQGroupEventHandler import QQGroupEventHandler

commands = {
  "/cat":"云吸猫",
  "/gakki":"云吸gakki",
  "/10":"云吸十元",
  "/bird":"云吸飞鸟",
  "/image":"獭獭传图",
  "/comment":"给作者留言",
  "/about":"关于此项目",
  "/donate":"援助作者",
  "/random":"掷骰子",
  "/anime":"以图搜番（\"/anime 图片\"）",
  "/gate":"挖宝选门（\"/gate 3\"）",
  "/search":"在最终幻想XIV中查询物品(\"/search 神龙\")",
  "/weather":"天气信息（快捷命令\"/fog\",\"/heat_wave\",\"/thunder\",\"/blizzard\"）",
  "/dps":"查询国际服同期DPS排名（\"/dps 8s 骑士\"）",
  "/raid":"查询零式英雄榜（\"/raid 蓝色裂痕 萌芽池\"）",
  "/nuannuan":"查看本周金蝶暖暖作业",
  "/gif":"生成沙雕图（\"/gif help\"）",
  "/dice":"DnD掷骰子（\"/dice 3d12\"）",
  "/bot":"机器人推送功能（\"/bot token 123\"）",
  "/pixiv":"Pixiv相关功能（\"/pixiv help\"）",
  "/music":"网易云音乐搜索（\"/music 届不到的恋\"）",
  "/duilian":"对联（\"/duilian 稻花香里说丰年\"）",
  "/hso":"好色哦"
}

group_commands = {
  "/group":"群相关功能控制",
  "/welcome":"设置欢迎语",
  "/custom_reply":"添加自定义命令",
  "/repeat_ban":"复读姬口球系统",
  "/repeat":"开启复读姬系统",
  "/left_reply":"聊天限额剩余情况",
  "/ban":"投票禁言",
  "/revenge":"复仇",
  "/vote":"投票系统",
  "/weibo":"微博订阅系统",
  "/command":"群功能停用/启用",
}

alter_commands = {
  "/pzz":"/weather 优雷卡常风之地 强风",
  "/blizzard":"/weather 优雷卡恒冰之地 暴雪",
  "/fog":"/weather 优雷卡恒冰之地 薄雾",
  "/thunder":"/weather 优雷卡恒冰之地 打雷",
  "/heat_wave":"/weather 优雷卡恒冰之地 热风",
  "/register_group":"/group register",
  "/welcome_demo":"/welcome demo",
  "/set_welcome_msg":"/welcome set",
  "/add_custom_reply list":"/custom_reply list",
  "/add_custom_reply":"/custom_reply add",
  "/del_custom_reply":"/custom_reply del",
  "/set_repeat_ban":"/repeat_ban set",
  "/disable_repeat_ban":"/repeat_ban disable",
  "/set_left_reply_cnt":"/left_reply set",
  "/set_ban":"/ban set",
  "/revenge_confirm":"/revenge confirm",
}

from .QQCommand_cat import QQCommand_cat
from .QQCommand_gakki import QQCommand_gakki
from .QQCommand_10 import QQCommand_10
from .QQCommand_bird import QQCommand_bird
from .QQCommand_comment import QQCommand_comment
from .QQCommand_search import QQCommand_search
from .QQCommand_about import QQCommand_about
from .QQCommand_donate import QQCommand_donate
from .QQCommand_anime import QQCommand_anime
from .QQCommand_gate import QQCommand_gate
from .QQCommand_random import QQCommand_random
from .QQCommand_weather import QQCommand_weather
from .QQCommand_gif import QQCommand_gif
from .QQCommand_dps import QQCommand_dps
from .QQCommand_dice import QQCommand_dice
from .QQCommand_hso import QQCommand_hso
from .QQCommand_raid import QQCommand_raid
from .QQCommand_bot import QQCommand_bot
from .QQCommand_pixiv import QQCommand_pixiv
from .QQCommand_music import QQCommand_music
from .QQCommand_duilian import QQCommand_duilian
from .QQCommand_image import QQCommand_image
from .QQCommand_nuannuan import QQCommand_nuannuan


from .QQGroupCommand_group import QQGroupCommand_group
from .QQGroupCommand_welcome import QQGroupCommand_welcome
from .QQGroupCommand_custom_reply import QQGroupCommand_custom_reply
from .QQGroupCommand_repeat_ban import QQGroupCommand_repeat_ban
from .QQGroupCommand_repeat import QQGroupCommand_repeat
from .QQGroupCommand_left_reply import QQGroupCommand_left_reply
from .QQGroupCommand_ban import QQGroupCommand_ban
from .QQGroupCommand_revenge import QQGroupCommand_revenge
from .QQGroupCommand_vote import QQGroupCommand_vote
from .QQGroupCommand_weibo import QQGroupCommand_weibo
from .QQGroupCommand_command import QQGroupCommand_command


from .QQGroupChat import QQGroupChat