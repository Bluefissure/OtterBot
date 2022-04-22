import copy
import time
import json
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max
from ffxivbot.models import Monster, Server, HuntLog, HuntGroup
from .ren2res import ren2res
import traceback

def gen_hunts(user, sonar=False):
    hunt_list = []
    resource_groups = set()
    TIMEFORMAT_MDHMS = "%m-%d %H:%M:%S"
    if not sonar:
        latest_kill_logs = HuntLog.objects.filter(
            Q(hunt_group__group__member_list__contains=user.user_id, log_type='kill') | Q(hunt_group__public=True)
        ).values('server__name', 'monster', 'hunt_group', 'instance_id').annotate(Max('time'))
    else:
        latest_kill_logs = HuntLog.objects.filter(log_type='sonar')\
            .values('server__name', 'monster', 'instance_id').annotate(Max('time'))
    maintain_logs = HuntLog.objects.filter(log_type='maintain').values('server__name').annotate(Max('time'))
    server_maintains = {}
    for log in maintain_logs:
        server_maintains[log['server__name']] = log['time__max']
    monster_dict = {}
    for monster in Monster.objects.all():
        monster_dict[monster.id] = monster
    for latest_kill_log in latest_kill_logs:
        try:
            if not sonar:
                hunt_group = HuntGroup.objects.get(id=latest_kill_log['hunt_group'])
            else:
                hunt_group = "Sonar"
            server_name = latest_kill_log['server__name']
            monster = monster_dict.get(latest_kill_log['monster'])
            maintain_finish_time = server_maintains.get(server_name, 0)
            resource_groups.add(str(hunt_group))
            last_kill_time = latest_kill_log['time__max']
            maintained = (maintain_finish_time > last_kill_time)
            kill_time = max(last_kill_time, maintain_finish_time)
            spawn_cooldown = (monster.first_spawn_cooldown if maintained else monster.spawn_cooldown)
            pop_cooldown = (monster.first_pop_cooldown if maintained else monster.pop_cooldown)
            next_spawn_time = kill_time + spawn_cooldown
            next_pop_time = kill_time + pop_cooldown
            cd_schedulef = spawn_cooldown / pop_cooldown
            schedulef = (time.time() - kill_time) / pop_cooldown
            cd_schedule = "{:.2%}".format(cd_schedulef)
            schedule = "{:.2%}".format(schedulef)
            if schedulef >= cd_schedulef:
                schedule_diff = schedulef - cd_schedulef
                schedule_diff = "{:.2%}".format(schedule_diff)
            else:
                schedule_diff = ""
            server_tag = server2tag(server_name)
            if next_spawn_time >= time.time():
                in_cd = "notcd"
            else:
                in_cd = ""
            monster_info = {}
            monster_info["monster"] = monster.cn_name
            monster_info["instance"] = latest_kill_log['instance_id']
            if monster.cn_name.endswith('2') and latest_kill_log['instance_id'] != 2:
                monster_info["instance"] = "2"
            if monster.cn_name.endswith('3') and latest_kill_log['instance_id'] != 3:
                monster_info["instance"] = "3"
            if monster_info["instance"] == 2 and not monster.cn_name.endswith('2'):
                monster_info["monster"] += "2"
            if monster_info["instance"] == 3 and not monster.cn_name.endswith('3'):
                monster_info["monster"] += "3"
            monster_info["server"] = server_name
            monster_info["territory"] = monster.territory
            monster_info["server_tag"] = server_tag
            monster_info["monster_type"] = monster.rank
            monster_info["schedule_diff"] = schedule_diff
            monster_info["cd_schedulef"] = cd_schedulef
            monster_info["cd_schedule"] = cd_schedule
            monster_info["schedulef"] = schedulef
            monster_info["schedule"] = schedule
            monster_info["in_cd"] = in_cd
            monster_info["kill_time"] = time.strftime(TIMEFORMAT_MDHMS, time.localtime(kill_time))
            monster_info["next_spawn_time"] = time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_spawn_time))
            monster_info["next_pop_time"] = time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_pop_time))
            monster_info["info"] = monster.info
            monster_info["resource"] = str(hunt_group)
            hunt_list.append(monster_info)
        except Exception as e:
            traceback.print_exc()
    return hunt_list, resource_groups


@login_required(login_url='/login/')
def hunt(req):
    hunt_list, resource_groups = gen_hunts(req.user.qquser, False)
    return ren2res('hunt.html', req, {"hunt_list": hunt_list, "resources": ", ".join(list(resource_groups))})

#@login_required(login_url='/login/')
def hunt_sonar(req):
    hunt_list, resource_groups = gen_hunts(None, True)
    return ren2res('hunt.html', req, {"hunt_list": hunt_list, "resources": ", ".join(list(resource_groups))})

NAME_TAG = {
    "红玉海":"hyh",
    "神意之地":"syzd",
    "幻影群岛":"hyqd",
    "拉诺西亚":"lnxy",
    "萌芽池":"myc",
    "宇宙和音":"yzhy",
    "沃仙曦染":"wxxr",
    "晨曦王座":"cxwz",
    "潮风亭":"cft",
    "神拳痕":"sqh",
    "白银乡":"byx",
    "白金幻象":"bjhx",
    "旅人栈桥":"lrzq",
    "拂晓之间":"fxzj",
    "龙巢神殿":"lcsd",
    "紫水栈桥":"zszq",
    "延夏":"yx",
    "静语庄园":"jyzy",
    "摩杜纳":"mdn",
    "海猫茶屋":"hmcw",
    "柔风海湾":"rfhw",
    "琥珀原":"hpy",
    "梦羽宝境":"mybj",
    "水晶塔":"sjt",
    "银泪湖":"ylh",
    "太阳海岸":"tyha",
    "伊修加德":"yxjd",
    "红茶川":"hcc",
}

# What's the point???
def server2tag(server_name):
    return NAME_TAG.get(server_name, "Unknown")
