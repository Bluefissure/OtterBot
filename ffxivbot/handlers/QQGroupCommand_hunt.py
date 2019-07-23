from django.utils.datetime_safe import datetime
from django.db.models import Q
from ffxivbot.handlers.QQUtils import *
from ffxivbot.models import *

def handle_special_mob(monster, next_spawn_time, next_pop_time):
    if monster.cn_name == "咕尔呱洛斯":
        nst_eorzea_day = getEorzeaDay(next_spawn_time)
        nct_eorzea_day = getEorzeaDay(next_pop_time)
        if nst_eorzea_day < 17:
            next_spawn_time = (getEorzeaYear(next_spawn_time) * 12 * 32 * 24 * 175) + (
                        getEorzeaMonth(next_spawn_time) * 32 * 24 * 175) + (
                                          16 * 24 * 175) + (17 * 175)
        elif nst_eorzea_day > 20:
            next_spawn_time = (getEorzeaYear(next_spawn_time) * 12 * 32 * 24 * 175) + (
                        (getEorzeaMonth(next_spawn_time) + 1) * 32 * 24 * 175) + (
                                          16 * 24 * 175) + (17 * 175)
        if nct_eorzea_day < 17:
            next_pop_time = (getEorzeaYear(
                next_pop_time) * 12 * 32 * 24 * 175) + (getEorzeaMonth(
                next_pop_time) * 32 * 24 * 175) + (16 * 24 * 175) + (17 * 175)
        elif nct_eorzea_day >= 17 and nst_eorzea_day <= 20:
            next_pop_time = next_spawn_time
        elif nct_eorzea_day > 20:
            next_pop_time = (getEorzeaYear(
                next_pop_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                next_pop_time) + 1) * 32 * 24 * 175) + (16 * 24 * 175) + (17 * 175)
    elif monster.cn_name == "夺心魔":
        nst_eorzea_day = getEorzeaDay(next_spawn_time)
        nct_eorzea_day = getEorzeaDay(next_pop_time)
        if nst_eorzea_day > 4:
            next_spawn_time = (getEorzeaYear(next_spawn_time) * 12 * 32 * 24 * 175) + (
                        (getEorzeaMonth(next_spawn_time) + 1) * 32 * 24 * 175)
        if nct_eorzea_day >= 1 and nst_eorzea_day <= 4:
            next_pop_time = next_spawn_time
        elif nct_eorzea_day > 4:
            next_pop_time = (getEorzeaYear(
                next_pop_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                next_pop_time) + 1) * 32 * 24 * 175)
    elif monster.cn_name == "巨大鳐":
        nst_eorzea_day = getEorzeaDay(next_spawn_time)
        nct_eorzea_day = getEorzeaDay(next_pop_time)
        if nst_eorzea_day < 17:
            next_spawn_time = (getEorzeaYear(next_spawn_time) * 12 * 32 * 24 * 175) + (
                        getEorzeaMonth(next_spawn_time) * 32 * 24 * 175) + (
                                          16 * 24 * 175) + (12 * 175)
        elif nst_eorzea_day > 20:
            next_spawn_time = (getEorzeaYear(next_spawn_time) * 12 * 32 * 24 * 175) + (
                        (getEorzeaMonth(next_spawn_time) + 1) * 32 * 24 * 175) + (
                                          16 * 24 * 175) + (12 * 175)
        if nct_eorzea_day < 17:
            next_pop_time = (getEorzeaYear(
                next_pop_time) * 12 * 32 * 24 * 175) + (getEorzeaMonth(
                next_pop_time) * 32 * 24 * 175) + (16 * 24 * 175) + (12 * 175)
        elif nct_eorzea_day >= 17 and nst_eorzea_day <= 20:
            next_pop_time = next_spawn_time
        elif nct_eorzea_day > 20:
            next_pop_time = (getEorzeaYear(
                next_pop_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                next_pop_time) + 1) * 32 * 24 * 175) + (16 * 24 * 175) + (12 * 175)
    return next_spawn_time, next_pop_time


def QQGroupCommand_hunt(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        group = kwargs["group"]
        user_info = kwargs["user_info"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        group = kwargs["group"]
        msg = ""

        receive_msg = receive["message"].replace("/hunt", "", 1).strip()
        param_segs = receive_msg.split(" ")
        TIMEFORMAT_MDHMS = "%m-%d %H:%M:%S"
        TIMEFORMAT_YMDHMS = "%Y-%m-%d %H:%M:%S"
        hunt_group = group.hunt_group.all()
        if hunt_group:
            # 检测是否狩猎组群组，并且获取群组信息
            hunt_group = hunt_group[0]
            while "" in param_segs:
                param_segs.remove("")
            try:
                optype = param_segs[0].strip()
            except IndexError:
                optype = "help"
            if (optype == "help"):
                msg = "獭獭の狩猎时钟 alpha.2\n\
/hunt help：帮助\n\
/hunt check：查询相关\n\
/hunt kill：设置击杀时间相关\n\
/hunt edit：手动修改相关\n\
/hunt list：列出相关\n\
/hunt maintained：设置为维护后状态（建议维护结束后立即使用）"
            elif (optype == "check"):
                try:
                    monster_name = param_segs[1].strip()
                    monster = Monster.objects.filter(Q(name=monster_name) | Q(cn_name=monster_name))
                    if monster:
                        # 获取怪物在各个服务器的击杀时间
                        latest_kill_log = hunt_group.hunt_log.filter(log_type="kill").latest('time')
                        last_kill_time = latest_kill_log.time
                        global_maintain_log = HuntLog.objects.filter(server=hunt_group.server, log_type="maintain").latest('time')
                        maintain_finish_time = global_maintain_log.time
                        maintained = (maintain_finish_time > last_kill_time)
                        kill_time = max(last_kill_time, maintain_finish_time)
                        spawn_cooldown = (monster.first_spawn_cooldown if maintained else monster.spawn_cooldown)
                        pop_cooldown = (monster.first_pop_cooldown if maintained else monster.pop_cooldown)
                        next_spawn_time = kill_time + spawn_cooldown
                        next_pop_time = kill_time + pop_cooldown
                        schedulef = (time.time() - kill_time) / pop_cooldown
                        schedule = "{:.2%}".format(schedulef)
                        next_spawn_time, next_pop_time = handle_special_mob(monster, next_spawn_time, next_pop_time)
                        msg = "{} {} {}\n".format(monster.territory, monster.cn_name, hunt_group.server) + \
                                "进度：{}\n".format(schedule) + \
                                "上次击杀时间：{}\n".format(time.strftime(TIMEFORMAT_MDHMS, time.localtime(kill_time))) + \
                                "开始触发时间：{}\n".format(time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_spawn_time))) + \
                                "必定触发时间：{}\n".format(time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_pop_time))) + \
                                "触发方法：{}".format(monster.info)
                    else:
                        msg = "找不到狩猎怪\"{}\"".format(monster_name)
                except IndexError:
                    msg = "狩猎时钟check命令示例：\n\
/hunt check [怪物名称]\n\
查询怪物的击杀时间、触发时间、触发说明等信息\n\
注：触发时间已经计算好触发条件的日期和天气等条件"
            elif (optype == "kill"):
                try:
                    monster_name = param_segs[1].strip()
                    monster = Monster.objects.filter(Q(name=monster_name) | Q(cn_name=monster_name))
                    if monster:
                        log = HuntLog(monster=monster, hunt_group=hunt_group, log_type="kill", time=time.time())
                        log.save()
                        msg = "{}的\"{}\"击杀时间已记录".format(hunt_group.server, monster)
                    else:
                        msg = "找不到狩猎怪\"{}\"".format(monster_name)
                except IndexError:
                    msg = "狩猎时钟list命令示例：\n/hunt kill [怪物名称]\n设置怪物的击杀时间为现在"
            elif (optype == "list"):
                try:
                    setype = param_segs[1].strip()
                    if setype == "cd":
                        a = 1
                        msg = ""
                        cd_msg_list = []
                        qcd_msg_list = []
                        all_monsters = Monster.objects.all()
                        for monster in all_monsters:
                            # 获取怪物在各个服务器的击杀时间
                            latest_kill_log = hunt_group.hunt_log.filter(log_type="kill").latest('time')
                            last_kill_time = latest_kill_log.time
                            global_maintain_log = HuntLog.objects.filter(server=hunt_group.server, log_type="maintain").latest('time')
                            maintain_finish_time = global_maintain_log.time
                            maintained = (maintain_finish_time > last_kill_time)
                            kill_time = max(last_kill_time, maintain_finish_time)
                            spawn_cooldown = (monster.first_spawn_cooldown if maintained else monster.spawn_cooldown)
                            pop_cooldown = (monster.first_pop_cooldown if maintained else monster.pop_cooldown)
                            next_spawn_time = kill_time + spawn_cooldown
                            next_pop_time = kill_time + pop_cooldown
                            schedulef = (time.time() - kill_time) / pop_cooldown
                            schedule = "{:.2%}".format(schedulef)
                            next_spawn_time, next_pop_time = handle_special_mob(monster, next_spawn_time, next_pop_time)
                            if next_spawn_time <= time.time():
                                cd_msg_list.append("{} {} {}\n{}".format(monster.territory, monster.cn_name, schedule,
                                    time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_spawn_time))))
                            elif next_spawn_time - 3600 < time.time() < next_spawn_time:
                                qcd_msg_list.append("{} {} {}\n{}".format(monster.territory, monster.cn_name, schedule,
                                    time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_spawn_time))))
                            msg = "可以触发的S怪：\n"
                            msg += "\n".join(cd_msg_list)
                            if qcd_msg_list:
                                msg += "\n准备进入触发时间的S怪（1小时内）：\n"
                                msg += "\n".join(qcd_msg_list)
                except IndexError:
                    msg = "狩猎时钟list命令示例：\n/hunt list [选项]\n选项解释：\ncd：列出可触发的s"
            elif ("maintain" in optype):
                if "global" in optype:
                    for server in Server.objects.all():
                        log = HuntLog(hunt_group=hunt_group, server=server, log_type="maintain", time=time.time())
                        log.save()
                        msg = "全体服务器的狩猎怪击杀时间已重置"
                else:
                    log = HuntLog(hunt_group=hunt_group, server=hunt_group.server, log_type="maintain", time=time.time())
                    log.save()
                    msg = "{} 的狩猎怪击杀时间已重置".format(hunt_group.server)
            elif (optype == "edit"):
                try:
                    monster_name = param_segs[1].strip()
                    YMD = param_segs[2].strip()
                    HMS = param_segs[3].strip()
                    monster = Monster.objects.filter(Q(name=monster_name) | Q(cn_name=monster_name))
                    if monster:
                        latest_kill_log = hunt_group.hunt_log.filter(monster=monster, log_type="kill").latest('time')
                        kill_time = latest_kill_log.time
                        edittimestr = YMD + " " + HMS
                        edittime = int(time.mktime(time.strptime(edittimestr, TIMEFORMAT_YMDHMS)))
                        latest_kill_log.time = edittime
                        latest_kill_log.save(update_fields=["time"])
                        msg = latest_kill_log.get_info() + "\n击杀时间已修改为：\n" + edittimestr
                    else:
                        msg = "找不到狩猎怪\"{}\"".format(monster_name)
                except IndexError:
                    msg = "狩猎时钟edit命令示例：\n/hunt edit [怪物名称] [时间]\n时间格式例：\n1970-01-01 00:00:00"
        else:
            msg = "该群并非狩猎组群组"
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc(e)
    return action_list
