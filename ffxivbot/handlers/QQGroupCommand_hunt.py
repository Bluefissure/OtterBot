from django.db.models import Q

from ffxivbot.handlers.QQUtils import *
from ffxivbot.models import *

import logging


def monster_kill(monster_name, hunt_group, server_info, edittime):
    TIMEFORMAT_YMDHMS = "%Y-%m-%d %H:%M:%S"
    time_str = time.strftime(TIMEFORMAT_YMDHMS, time.localtime(edittime))
    monster = Monster.objects.filter(Q(name=monster_name) | Q(cn_name=monster_name))
    if monster.exists():
        monster = monster[0]
        log = HuntLog(
            monster=monster,
            hunt_group=hunt_group,
            server=server_info,
            log_type="kill",
            time=edittime,
        )
        log.save()
        msg = '{}的"{}"击杀时间已记录\n记录时间：{}'.format(server_info.name, monster, time_str)
        logging.info("hunt_group:{}\nmsg:{}".format(hunt_group, msg))
    else:
        msg = '找不到狩猎怪"{}"'.format(monster_name)
    return msg


def log_revoke(monster_name, hunt_group, server_info):
    monster = Monster.objects.filter(Q(name=monster_name) | Q(cn_name=monster_name))
    if monster.exists():
        monster = monster[0]
        try:
            latest_kill_log = HuntLog.objects.filter(
                hunt_group=hunt_group,
                monster=monster,
                server=server_info,
                log_type="kill",
            ).latest("id")
        except HuntLog.DoesNotExist:
            msg = "已达到了最初状态"
        else:
            msg = "已删除：\n{}".format(latest_kill_log.get_info())
            latest_kill_log.delete()
            log = HuntLog(
                monster=monster,
                hunt_group=hunt_group,
                server=server_info,
                log_type="revoke",
                time=time.time(),
            )
            log.save()

    else:
        msg = '找不到狩猎怪"{}"'.format(monster_name)
    return msg


# def monster_edit_bak(monster_name, hunt_group, server_info, YMD, HMS):
#     TIMEFORMAT_YMDHMS = "%Y-%m-%d %H:%M:%S"
#     monster = Monster.objects.filter(Q(name=monster_name) | Q(cn_name=monster_name))
#     if monster.exists():
#         monster = monster[0]
#         edittimestr = YMD + " " + HMS
#         edittime = int(time.mktime(time.strptime(edittimestr, TIMEFORMAT_YMDHMS)))
#         try:
#             latest_kill_log = HuntLog.objects.filter(monster=monster, server=server_info, log_type="kill").latest(
#                 'time')
#         except HuntLog.DoesNotExist:
#             log = HuntLog(hunt_group=hunt_group,
#                           server=server_info,
#                           monster=monster,
#                           log_type="kill",
#                           time=edittime
#                           )
#             log.save()
#             msg = "\"{}\"击杀时间已修改为：\n{}".format(monster, edittimestr)
#         else:
#             if latest_kill_log.time > edittime:
#                 latest_kill_log.time = edittime
#             latest_kill_log.save(update_fields=["time"])
#             msg = latest_kill_log.get_info() + "\n击杀时间已修改为：\n" + edittimestr
#     else:
#         msg = "找不到狩猎怪\"{}\"".format(monster_name)
#     return msg


def handle_special_mob(monster, next_spawn_time):
    now_time = time.time()
    trigger_time_info = ""
    next_trigger_time = time.time()
    ntt_eorzea_day = getEorzeaDay(now_time)
    if monster.cn_name.startswith("咕尔呱洛斯"):
        if ntt_eorzea_day < 17:
            next_trigger_time = (
                (getEorzeaYear(now_time) * 12 * 32 * 24 * 175)
                + (getEorzeaMonth(now_time) * 32 * 24 * 175)
                + (15 * 24 * 175)
                + (17 * 175)
            )
        elif ntt_eorzea_day >= 17 and ntt_eorzea_day <= 20:
            next_trigger_time = now_time
        elif ntt_eorzea_day > 20:
            next_trigger_time = (
                (getEorzeaYear(now_time) * 12 * 32 * 24 * 175)
                + ((getEorzeaMonth(now_time) + 1) * 32 * 24 * 175)
                + (15 * 24 * 175)
                + (17 * 175)
            )
        if next_trigger_time > next_spawn_time:
            trigger_time_info = "\n（触发时间计算为ET当月第16天17:00）"
            get_trigger_time = next_trigger_time
    elif monster.cn_name.startswith("夺心魔"):
        if ntt_eorzea_day >= 1 and ntt_eorzea_day <= 4:
            next_trigger_time = now_time
        elif ntt_eorzea_day > 4:
            next_trigger_time = (getEorzeaYear(now_time) * 12 * 32 * 24 * 175) + (
                (getEorzeaMonth(now_time) + 1) * 32 * 24 * 175
            )
        if next_trigger_time > next_spawn_time:
            trigger_time_info = "\n（触发时间计算为ET当月第1天00:00）"
            get_trigger_time = next_trigger_time
    elif monster.cn_name.startswith("巨大鳐"):
        if ntt_eorzea_day < 17:
            next_trigger_time = (
                (getEorzeaYear(now_time) * 12 * 32 * 24 * 175)
                + (getEorzeaMonth(now_time) * 32 * 24 * 175)
                + (15 * 24 * 175)
                + (12 * 175)
            )
        elif ntt_eorzea_day >= 17 and ntt_eorzea_day <= 20:
            next_trigger_time = now_time
        elif ntt_eorzea_day > 20:
            next_trigger_time = (
                (getEorzeaYear(now_time) * 12 * 32 * 24 * 175)
                + ((getEorzeaMonth(now_time) + 1) * 32 * 24 * 175)
                + (15 * 24 * 175)
                + (12 * 175)
            )
        if next_trigger_time > next_spawn_time:
            trigger_time_info = "\n（触发时间计算为ET当月第16天12:00）"
            get_trigger_time = next_trigger_time
    elif monster.cn_name.startswith("伽洛克"):
        # 算法有问题，待更新
        a = 0
        garlok_spawn_weathers = getFollowingWeathers(
            territory=monster.territory,
            cnt=1000,
            TIMEFORMAT="%Y-%m-%d %H:%M:%S",
            unixSeconds=now_time,
            Garlok=True,
        )
        for spawn_weather in garlok_spawn_weathers:
            if (
                spawn_weather["name"] == "碧空"
                or spawn_weather["name"] == "晴朗"
                or spawn_weather["name"] == "阴云"
                or spawn_weather["name"] == "薄雾"
            ):
                a += 1
            else:
                a = 0
            if a == 9:
                next_trigger_time = int(
                    time.mktime(time.strptime(spawn_weather["LT"], "%Y-%m-%d %H:%M:%S"))
                )
                break
        if next_trigger_time > next_spawn_time:
            trigger_time_info = "\n（触发时间计算为连续不下雨的ET 第9天的00:00）"
            get_trigger_time = next_trigger_time
    elif monster.cn_name.startswith("雷德罗巨蛇"):
        Laider_spawn_weathers = getFollowingWeathers(
            territory=monster.territory,
            cnt=1000,
            TIMEFORMAT="%Y-%m-%d %H:%M:%S",
            unixSeconds=now_time,
        )
        for spawn_weather in Laider_spawn_weathers:
            if spawn_weather["name"] == "小雨" and spawn_weather["pre_name"] == "小雨":
                next_trigger_time = int(
                    time.mktime(time.strptime(spawn_weather["LT"], "%Y-%m-%d %H:%M:%S"))
                ) + (2 * 175)
                break
        if next_trigger_time > next_spawn_time:
            trigger_time_info = "\n（触发时间计算为两次雨天后的ET 2小时后）"
            get_trigger_time = next_trigger_time
    if trigger_time_info == "":
        special_msg = ""
    else:
        special_msg = "\n下次触发时间：{}".format(
            time.strftime("%m-%d %H:%M:%S", time.localtime(get_trigger_time))
        )
    return special_msg, trigger_time_info


def QQGroupCommand_hunt(*args, **kwargs):
    # global server_info
    action_list = []
    try:
        action_list = []
        receive = kwargs["receive"]
        user_id = receive["user_id"]
        user_info = kwargs["user_info"]
        group = kwargs["group"]
        msg = ""

        receive_msg = receive["message"].replace("/hunt", "", 1).strip()
        param_segs = receive_msg.split(" ")
        while "" in param_segs:
            param_segs.remove("")
        TIMEFORMAT_MDHMS = "%m-%d %H:%M:%S"
        TIMEFORMAT_YMDHMS = "%Y-%m-%d %H:%M:%S"
        TIMEFORMAT_YMDHMS0 = "%Y/%m/%d %H:%M:%S"
        hunt_group = group.hunt_group.all()
        if hunt_group.exists():
            # 检测是否狩猎组群组，并且获取群组信息
            hunt_group = hunt_group[0]
            while "" in param_segs:
                param_segs.remove("")
            try:
                optype = param_segs[0].strip()
            except IndexError:
                optype = "help"
            if optype == "help":
                msg = "獭獭の狩猎时钟 beta.1\n\
/hunt help：帮助\n\
/hunt public：切换公开\n\
/hunt check：查询相关\n\
/hunt kill：设置击杀时间相关\n\
/hunt edit：手动修改相关\n\
/hunt list：列出相关\n\
/hunt maintain：设置当前服务器为维护后状态\n\
/hunt maintain_global：设置全体服务器为维护后状态"
            elif optype == "check":
                try:
                    monster_name = param_segs[1].strip()
                    try:
                        # 待增加nickname
                        server_name = param_segs[2].strip()
                    except IndexError:
                        server_name = hunt_group.server
                    server_info = Server.objects.filter(name=server_name)
                    if server_info.exists():
                        server_info = server_info[0]
                        monster = Monster.objects.filter(
                            Q(name=monster_name) | Q(cn_name=monster_name)
                        )
                        if monster.exists():
                            monster = monster[0]
                            try:
                                # latest_kill_log = hunt_group.hunt_log.filter(monster=monster, log_type="kill").latest("id")
                                latest_kill_log = HuntLog.objects.filter(
                                    hunt_group=hunt_group,
                                    monster=monster,
                                    server=server_info,
                                    log_type="kill",
                                ).latest("id")
                                last_kill_time = latest_kill_log.time
                            except HuntLog.DoesNotExist as e:
                                last_kill_time = 0
                            try:
                                global_maintain_log = HuntLog.objects.filter(
                                    hunt_group=hunt_group,
                                    server=server_info,
                                    log_type="maintain",
                                ).latest("id")
                                maintain_finish_time = global_maintain_log.time
                            except HuntLog.DoesNotExist as e:
                                maintain_finish_time = 0
                            maintained = maintain_finish_time > last_kill_time
                            kill_time = max(last_kill_time, maintain_finish_time)
                            spawn_cooldown = (
                                monster.first_spawn_cooldown
                                if maintained
                                else monster.spawn_cooldown
                            )
                            pop_cooldown = (
                                monster.first_pop_cooldown
                                if maintained
                                else monster.pop_cooldown
                            )
                            next_spawn_time = kill_time + spawn_cooldown
                            next_pop_time = kill_time + pop_cooldown
                            schedulef = (time.time() - kill_time) / pop_cooldown
                            schedule = "{:.2%}".format(schedulef)
                            # next_spawn_time, next_pop_time = handle_special_mob(monster, next_spawn_time, next_pop_time)
                            special_msg, trigger_time_info = handle_special_mob(
                                monster, next_spawn_time
                            )
                            if server_name:
                                msg = (
                                    "{} {} {}\n".format(
                                        monster.territory, monster.cn_name, server_name
                                    )
                                    + "进度：{}\n".format(schedule)
                                    + "上次击杀时间：{}\n".format(
                                        time.strftime(
                                            TIMEFORMAT_MDHMS, time.localtime(kill_time)
                                        )
                                    )
                                    + "开始触发时间：{}\n".format(
                                        time.strftime(
                                            TIMEFORMAT_MDHMS,
                                            time.localtime(next_spawn_time),
                                        )
                                    )
                                    + "高概率触发时间：{}\n".format(
                                        time.strftime(
                                            TIMEFORMAT_MDHMS,
                                            time.localtime(next_pop_time),
                                        )
                                    )
                                    + "触发方法：{}\n".format(monster.info)
                                    + "{}".format(special_msg)
                                    + "{}".format(trigger_time_info)
                                )
                            else:
                                msg = (
                                    "{} {} {}\n".format(
                                        monster.territory,
                                        monster.cn_name,
                                        hunt_group.server,
                                    )
                                    + "进度：{}\n".format(schedule)
                                    + "上次击杀时间：{}\n".format(
                                        time.strftime(
                                            TIMEFORMAT_MDHMS, time.localtime(kill_time)
                                        )
                                    )
                                    + "开始触发时间：{}\n".format(
                                        time.strftime(
                                            TIMEFORMAT_MDHMS,
                                            time.localtime(next_spawn_time),
                                        )
                                    )
                                    + "高概率触发时间：{}\n".format(
                                        time.strftime(
                                            TIMEFORMAT_MDHMS,
                                            time.localtime(next_pop_time),
                                        )
                                    )
                                    + "触发方法：{}\n".format(monster.info)
                                    + "{}".format(special_msg)
                                    + "{}".format(trigger_time_info)
                                )
                        else:
                            msg = '找不到狩猎怪"{}"'.format(monster_name)
                except IndexError:
                    msg = """狩猎时钟check命令示例：
/hunt check [怪物名称] <服务器>
查询怪物的击杀时间、触发时间、触发说明等信息
注：触发时间已经计算好触发条件的日期和天气等条件"""
            elif optype == "kill":
                try:
                    monster_name = param_segs[1].strip()
                    try:
                        # 待增加nickname
                        server_name = param_segs[2].strip()
                    except IndexError:
                        server_name = hunt_group.server.name
                    edittime = time.time()
                    server_info = Server.objects.filter(name=server_name)
                    if server_info.exists():
                        server_info = server_info[0]
                        # try:
                        #     test_get_server_group = HuntGroup.objects.get(server=server_info.id)
                        #     if server_name == hunt_group.server:
                        #         msg = monster_kill(monster_name, hunt_group, server_info, edittime)
                        #     else:
                        #         msg = "该群组已经有管理群组，无法编辑"
                        # except HuntGroup.DoesNotExist:
                        #     msg = monster_kill(monster_name, hunt_group, server_info, edittime)
                        msg = monster_kill(
                            monster_name, hunt_group, server_info, edittime
                        )
                except IndexError:
                    msg = "狩猎时钟list命令示例：\n/hunt kill [怪物名称] <服务器>\n设置怪物的击杀时间为现在\n仅可以修改本群组对应的服务器和没有管理群组的服务器"
            elif optype == "list":
                try:
                    setype = param_segs[1].strip()
                    if setype == "cd":
                        msg = ""
                        cd_msg_list = []
                        qcd_msg_list = []
                        all_monsters = Monster.objects.all()
                        try:
                            server_name = param_segs[2].strip()
                        except IndexError:
                            server_name = hunt_group.server
                        server_info = Server.objects.filter(name=server_name)
                        if server_info.exists():
                            server_info = server_info[0]
                            for monster in all_monsters:
                                # 获取怪物在各个服务器的击杀时间
                                try:
                                    latest_kill_log = HuntLog.objects.filter(
                                        hunt_group=hunt_group,
                                        monster=monster,
                                        server=server_info,
                                        log_type="kill",
                                    ).latest("id")
                                    last_kill_time = latest_kill_log.time
                                except HuntLog.DoesNotExist as e:
                                    last_kill_time = 0
                                try:
                                    global_maintain_log = HuntLog.objects.filter(
                                        hunt_group=hunt_group,
                                        server=server_info,
                                        log_type="maintain",
                                    ).latest("id")
                                    maintain_finish_time = global_maintain_log.time
                                except HuntLog.DoesNotExist as e:
                                    maintain_finish_time = 0
                                maintained = maintain_finish_time > last_kill_time
                                kill_time = max(last_kill_time, maintain_finish_time)
                                spawn_cooldown = (
                                    monster.first_spawn_cooldown
                                    if maintained
                                    else monster.spawn_cooldown
                                )
                                pop_cooldown = (
                                    monster.first_pop_cooldown
                                    if maintained
                                    else monster.pop_cooldown
                                )
                                next_spawn_time = kill_time + spawn_cooldown
                                next_pop_time = kill_time + pop_cooldown
                                schedulef = (time.time() - kill_time) / pop_cooldown
                                schedule = "{:.2%}".format(schedulef)
                                # next_spawn_time, next_pop_time = handle_special_mob(monster, next_spawn_time, next_pop_time)
                                special_msg, trigger_time_info = handle_special_mob(
                                    monster, next_spawn_time
                                )
                                if next_spawn_time <= time.time():
                                    cd_msg_list.append(
                                        "{} {} {}\n高概率触发时间：{} {}".format(
                                            monster.territory,
                                            monster.cn_name,
                                            schedule,
                                            time.strftime(
                                                TIMEFORMAT_MDHMS,
                                                time.localtime(next_pop_time),
                                            ),
                                            special_msg,
                                        )
                                    )
                                elif (
                                    next_spawn_time - 3600
                                    < time.time()
                                    < next_spawn_time
                                ):
                                    qcd_msg_list.append(
                                        "{} {} {}\n开始触发时间：{} {}".format(
                                            monster.territory,
                                            monster.cn_name,
                                            schedule,
                                            time.strftime(
                                                TIMEFORMAT_MDHMS,
                                                time.localtime(next_spawn_time),
                                            ),
                                            special_msg,
                                        )
                                    )
                            if cd_msg_list:
                                msg += "可以触发的s怪：\n"
                                for cd_msg in cd_msg_list:
                                    msg += "{}\n".format(cd_msg)
                                msg += "\n"
                            if qcd_msg_list:
                                msg += "准备进入触发时间的s怪（1小时内）：\n"
                                for qcd_msg in qcd_msg_list:
                                    msg += "{}\n".format(qcd_msg)
                            if (not cd_msg_list) and (not qcd_msg_list):
                                msg = "暂时莫得可以触发的s怪qwq"
                except IndexError:
                    msg = "狩猎时钟list命令示例：\n/hunt list [选项] <服务器>\n选项解释：\ncd：列出可触发的s"
            elif "maintain" in optype:
                if "global" in optype:
                    for server in Server.objects.all():
                        log = HuntLog(
                            hunt_group=hunt_group,
                            server=server,
                            log_type="maintain",
                            time=time.time(),
                        )
                        log.save()
                    msg = "全体服务器的狩猎怪击杀时间已重置"
                else:
                    try:
                        server_name = param_segs[1].strip()
                    except IndexError:
                        server_name = str(hunt_group.server)
                    server_info = Server.objects.filter(name=server_name)
                    server = (
                        server_info[0] if server_info.exists() else hunt_group.server
                    )
                    log = HuntLog(
                        hunt_group=hunt_group,
                        server=server,
                        log_type="maintain",
                        time=time.time(),
                    )
                    log.save()
                    msg = "{} 的狩猎怪击杀时间已重置".format(server)
            elif "initialize" in optype:
                # 其实可以不使用
                # 暂时不写入配置文件，如有自建，需要修改此处
                if user_id == 2875726738 or user_id == 306401806:
                    for server in Server.objects.all():
                        for monster in Monster.objects.all():
                            log = HuntLog(
                                monster=monster,
                                hunt_group=hunt_group,
                                server=server,
                                log_type="kill",
                                time=time.time(),
                            )
                            log.save()
                    msg = "时钟功能初始化成功"
            elif optype == "edit":
                try:
                    monster_name = param_segs[1].strip()
                    YMD = param_segs[2].strip()
                    HMS = param_segs[3].strip()
                    edittimestr = YMD + " " + HMS
                    edittime = int(
                        time.mktime(time.strptime(edittimestr, TIMEFORMAT_YMDHMS))
                    )
                    try:
                        server_name = param_segs[4].strip()
                    except IndexError:
                        server_name = hunt_group.server
                    server_info = Server.objects.filter(name=server_name)
                    if server_info.exists():
                        server_info = server_info[0]
                        if monster_name.startswith("maintain"):
                            if "global" in monster_name:
                                for server in Server.objects.all():
                                    log = HuntLog.objects.filter(
                                        hunt_group=hunt_group,
                                        server=server,
                                        log_type="maintain",
                                    ).latest("id")
                                    log.time = edittime
                                    log.save()
                                msg = "全体服务器维护时间被重置为{}".format(edittimestr)
                            else:
                                log = HuntLog.objects.filter(
                                    hunt_group=hunt_group,
                                    server=server_info,
                                    log_type="maintain",
                                ).latest("id")
                                log.time = edittime
                                log.save()
                                msg = "{}的维护时间被重置为{}".format(server_info, edittimestr)
                        else:
                            msg = monster_kill(
                                monster_name, hunt_group, server_info, edittime
                            )
                except IndexError:
                    msg = """狩猎时钟edit命令示例：
/hunt edit [怪物名称] [时间] <服务器>
/hunt edit maintain(_global) [时间] <服务器>
时间格式例：
1970-01-01 00:00:00"""
            elif optype == "revoke":
                try:
                    monster_name = param_segs[1].strip()
                    try:
                        server_name = param_segs[2].strip()
                    except IndexError:
                        server_name = hunt_group.server
                    server_info = Server.objects.filter(name=server_name)
                    if server_info.exists():
                        server_info = server_info[0]
                        # try:
                        #     test_get_server_group = HuntGroup.objects.get(server=server_info.id)
                        #     if server_name == hunt_group.server:
                        #         msg = log_revoke(monster_name, server_info)
                        #     else:
                        #         msg = "该群组已经有管理群组，无法编辑"
                        # except:
                        msg = log_revoke(monster_name, hunt_group, server_info)
                except IndexError:
                    msg = "*"
            elif optype == "public":
                if user_info["role"] != "owner":
                    msg = "仅群主有权限设置狩猎群组公开与否"
                else:
                    hunt_group.public = not hunt_group.public
                    hunt_group.save(update_fields=["public"])
                    msg = "本狩猎群组已被设置为{}群组".format("公开" if hunt_group.public else "私密")
        elif len(param_segs) == 2 and param_segs[0] == "register":
            servers = Server.objects.filter(name=param_segs[1])
            if user_info["role"] != "owner":
                msg = "仅群主有权限注册狩猎群组"
            elif not servers.exists():
                msg = '找不到服务器"{}"'.format(param_segs[1])
            else:
                server = servers[0]
                hg = HuntGroup(
                    name="{}-{}".format(group, server), group=group, server=server,
                )
                hg.save()
                msg = '狩猎群"{}"已建立'.format(hg.name)
        else:
            msg = '该群并非狩猎组群组，请使用"/hunt register 服务器"来注册狩猎群组'
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
        traceback.print_exc()
    return action_list
