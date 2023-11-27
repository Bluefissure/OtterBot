from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import csv
import datetime
import hashlib
from functools import cache
from typing import Union

# Legacy /luck
def luck_legacy(receive):
    user_id = receive["user_id"]
    random_num = get_page_num(user_id)
    luck_data = LuckData.objects.filter(number=random_num)
    if luck_data.exists():
        luck_data = luck_data.first()
        if "text" not in receive["message"]:
            img = luck_data.img_url
            return "[CQ:at,qq=%s]\n" % user_id + "[CQ:image,file={}]".format(img)
        else:
            return "[CQ:at,qq=%s]\n" % user_id + luck_data.text
    return "[CQ:at,qq=%s]\n" % user_id + "好像出了点问题，明天再试试吧~"

def get_page_num(QQnum):
    today = datetime.date.today()
    formatted_today = int(today.strftime('%y%m%d'))
    strnum = str(formatted_today * QQnum)

    md5 = hashlib.md5()
    md5.update(strnum.encode('utf-8'))
    res = md5.hexdigest()

    return int(res.upper(), 16) % 100 + 1

# New /luck
RESOURCE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "resources", "luck")
EVENT_LIST: list = []
EVENT_LIST_CONTENT: dict = {}
WAR, MAGIC, LAND, HAND, STAINS, JOB_ROLES = [], [], [], [], [], [[], [], [], [], []]

# 读取职业列表，计划返回4组list
@cache
def get_jobs() -> tuple:
    war_jobs = []
    magic_jobs = []
    land_jobs = []
    hand_jobs = []
    # 生产采集，坦克，近战，远程，治疗，分别为0-4
    jobs_role = [[], [], [], [], []]
    with open(os.path.join(RESOURCE_DIR, "ClassJob.csv"), mode="r", encoding="utf-8") as f:
        jobs_csv = csv.reader(f)
        for job in jobs_csv:
            if job[4] == "战斗精英":
                if job[1] == job[39].split("之")[0]:
                    # print(job[1])
                    war_jobs.append(job[1])
                    jobs_role[int(job[31])].append(job[1])
            elif job[4] == "魔法导师":
                if job[1] == job[39].split("之")[0]:
                    # print(job[1])
                    magic_jobs.append(job[1])
                    jobs_role[int(job[31])].append(job[1])
            elif job[4] == "能工巧匠":
                hand_jobs.append(job[1])
                jobs_role[int(job[31])].append(job[1])
            elif job[4] == "大地使者":
                land_jobs.append(job[1])
                jobs_role[int(job[31])].append(job[1])
    return war_jobs, magic_jobs, land_jobs, hand_jobs, jobs_role

# 读取染剂列表
@cache
def get_stain() -> list:
    stains = []
    with open(os.path.join(RESOURCE_DIR, "StainTransient.csv"), mode="r", encoding="utf-8") as f:
        stains_csv = csv.reader(f)
        for stain in stains_csv:
            if "染剂" in stain[1]:
                stains.append(stain[1])
    return stains


# 读取事件列表，以及对应一言
@cache
def get_event() -> dict:
    with open(os.path.join(RESOURCE_DIR, "events.json"), mode="r", encoding="utf-8") as f:
        events = json.load(f)
    # 每个event有一个组list，其中按从大到小顺序储存了对应的一言，默认luck为50，unluck为0
    # 为了后续判断，请将luck_event的数字满足 50<=num<=100; 而unluck满足 0<=num<50
    return events

# 特殊职业创建特殊语句
def sub_event(key: str) -> str:
    if key == "舞者":
        partner = WAR + MAGIC
        return key + "--> 最佳舞伴: " + random.choice(partner)
    elif key == "贤者":
        partner = JOB_ROLES[1]
        return key + "--> 最佳奶伴: " + random.choice(partner)
    return key

# 针对每个qq用户，通过QQ号和日期生成一个种子
def get_seed(qq_num: Union[int, str], redraw: bool = False) -> int:
    # 众所周知ff14玩家的一天从国内23:00开始
    utc_today = datetime.datetime.utcnow().replace(tzinfo=datetime.timezone.utc)
    ffxiv_today = utc_today.astimezone(datetime.timezone(datetime.timedelta(hours=9)))
    formatted_ffxiv_today = int(ffxiv_today.strftime('%y%m%d'))
    try:
        qq_num = int(qq_num)
    except ValueError:  # if qq_num is str and cannot be parsed to int
        qq_num = int(hashlib.sha256(qq_num.encode()).hexdigest(), 16) % (10 ** 10)
    if redraw:
        qq_num = (qq_num ** 2) % (10 ** 10)
    str_num = str(formatted_ffxiv_today * qq_num)
    md5 = hashlib.md5()
    md5.update(str_num.encode('utf-8'))
    res = md5.hexdigest()
    return int(res.upper(), 16) % 100 + 1

def get_hint(luck_number: str, luck_job: str, luck_event: str, unlucky_event: str, stain: str) -> str:
    luck_number = int(luck_number)
    # 根据一些特殊值生成语句
    special_event: str = ""
    if luck_number > 95:
        special_event += "是欧皇(*′▽｀)ノノ\n"
    elif luck_number < 5:
        special_event += "是非酋︿(￣︶￣)︿\n"
    elif luck_job == "占星术士":
        if luck_number > 80:
            special_event += "你抽卡必定日月星三连(￣︶￣)\n"
        elif luck_number < 20:
            special_event += "即使同色，也要勇敢的挑战命运ヾ(◍°∇°◍)ﾉﾞ\n"
    elif luck_job == "忍者":
        if luck_number > 70:
            special_event += "Duang Duang Duang 天地人一气呵成\n"
        elif luck_number < 20:
            special_event += "兔兔在头顶的样子很可爱的(✺ω✺)"
    if luck_number >= 50:
        events = EVENT_LIST_CONTENT[luck_event]
    else:
        events = EVENT_LIST_CONTENT[unlucky_event]
    # 根据每个event储存的一组list，来选择返回一言，要求达到第一个小于luck_number(运势)的值跳出
    event_content = ""
    for content in events:
        if content[0] <= luck_number:
            event_content = content[1]
            break
    if event_content == "":
        event_content = "诶诶，咱没有料到呢？肯定是笨蛋梦魇偷懒了[○･｀Д´･ ○]"
    return special_event + event_content

def init():
    global WAR, MAGIC, LAND, HAND, STAINS, JOB_ROLES, EVENT_LIST_CONTENT, EVENT_LIST
    # create constant vars
    WAR, MAGIC, LAND, HAND, JOB_ROLES = get_jobs()
    STAINS = get_stain()
    EVENT_LIST_CONTENT = get_event()
    EVENT_LIST = list(EVENT_LIST_CONTENT.keys())
    logging.info("占星术士成功拿到卡牌(启动初始化完成)")


def luck_daily(user_id: Union[int, str], redraw: bool = False, group_message: bool = True) -> str:
    if not all([WAR, MAGIC, LAND, HAND, STAINS]):
        init()
    # 生成当天种子, 重抽判断
    r = random.Random(get_seed(user_id, redraw))
    # content
    # @QQ 不需要，nonebot有命令
    # at = "[CQ:at,qq=%s]" % caller_qq_number
    # 运势 1-100
    luck_number: str = str(r.randint(1, 100))
    # 职业 ff14全部职业
    luck_job: str = sub_event(str(r.choice(WAR + MAGIC + LAND + HAND)))
    # 宜
    luck_event = r.choice(EVENT_LIST)
    # 忌
    unlucky_event_list: list = EVENT_LIST.copy()
    unlucky_event_list.remove(luck_event)
    unlucky_event: str = r.choice(unlucky_event_list)
    # 宜忌互锁 诸事 与 无
    if luck_event == "诸事":
        unlucky_event = "无"
    elif unlucky_event == "诸事":
        luck_event = "无"
    # 染剂
    stain: str = r.choice(STAINS)
    # 一言
    hint: str = get_hint(luck_number, luck_job, luck_event, unlucky_event, stain)
    # 群消息特殊化
    if group_message:
        message: str = "运势: " + luck_number + "%  幸运职业: " + luck_job + \
                       "\n宜: " + luck_event + "  忌: " + unlucky_event + "  幸运染剂: " + stain + "\n" + hint
    else:
        message: str = "运势: " + luck_number + "%\n幸运职业: " + luck_job + \
                       "\n宜: " + luck_event + "  忌: " + unlucky_event + "\n幸运染剂: " + stain + "\n" + hint
    return message

def luck(receive):
    user_id = receive["user_id"]
    message = receive["message"].replace("/luck", "").strip()
    msg_segs = message.split(" ")
    is_group = receive.get("group_id") is not None
    while "" in msg_segs:
        msg_segs.remove("")
    if len(msg_segs) == 0:
        msg = luck_daily(user_id=user_id, group_message=is_group)
        print(f"msg: {msg}")
    elif len(msg_segs) == 1 and (msg_segs[0].lower() == "redraw" or msg_segs[0].lower() == "r"):
        msg = luck_daily(user_id=user_id, redraw=True, group_message=is_group)
    elif len(msg_segs) == 1 and msg_segs[0].lower() == "help":
        msg = """使用命令 /luck 获得今日艾欧泽亚运势
对结果不满意，可以使用\"/luck r\"来重抽
重构自：onebot_Astrologian_FFXIV"""
    return "[CQ:at,qq=%s]\n" % user_id + msg.strip()



def QQCommand_luck(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        message = receive["message"]
        if message == "/luck legacy":
            msg = luck_legacy(receive)
        else:
            msg = luck(receive)
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        traceback.print_exc()
    return []