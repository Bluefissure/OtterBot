import copy
import time
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from ffxivbot.models import Monster, Server, HuntLog
from .ren2res import ren2res


@login_required(login_url='/login/')
def hunt(req):
    all_monsters = Monster.objects.all()
    all_servers = Server.objects.all()
    monster_info = {}
    hunt_list = []
    user = req.user.qquser
    resource_groups = set()
    TIMEFORMAT_MDHMS = "%m-%d %H:%M:%S"
    for server in all_servers:
        for monster in all_monsters:
            kill_logs = HuntLog.objects.filter(
                            hunt_group__group__member_list__contains=user.user_id,
                            monster=monster,
                            server=server,
                            log_type="kill")
            if not kill_logs:
                kill_logs = HuntLog.objects.filter(
                            hunt_group__public=True,
                            monster=monster,
                            server=server,
                            log_type="kill")
            if not kill_logs:
                continue
            latest_kill_log = kill_logs.latest("id")
            resource_groups.add(str(latest_kill_log.hunt_group))
            last_kill_time = latest_kill_log.time
            try:
                global_maintain_log = HuntLog.objects.filter(
                                            hunt_group__group__member_list__contains=user.user_id,
                                            server=server,
                                            log_type="maintain"
                                        ).latest("time")
                maintain_finish_time = global_maintain_log.time
            except HuntLog.DoesNotExist:
                maintain_finish_time = 0
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
            server_tag = server2tag(server.name)
            if next_spawn_time >= time.time():
                in_cd = "notcd"
            else:
                in_cd = ""
            monster_info["territory"] = monster.territory
            monster_info["monster"] = monster.cn_name
            monster_info["server"] = server
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
            monster_info["resource"] = str(latest_kill_log.hunt_group)
            hunt_list.append(copy.deepcopy(monster_info))
    return ren2res('hunt.html', req, {"hunt_list": hunt_list, "resources": ", ".join(list(resource_groups))})


def server2tag(server_name):
    name_tag = {
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
        "琥珀原":"hpy"
    }
    return name_tag.get(server_name, "unknown")
