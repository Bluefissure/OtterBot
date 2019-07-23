from django.utils.datetime_safe import datetime
from ffxivbot.handlers.QQUtils import *
from ffxivbot.models import *


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
        group_id = receive["group_id"]
        msg = ""

        receive_msg = receive["message"].replace("/hunt", "", 1).strip()
        param_segs = receive_msg.split(" ")
        TIMEFORMAT_MDHMS = "%m-%d %H:%M:%S"
        TIMEFORMAT_YMDHMS = "%Y-%m-%d %H:%M:%S"

        try:
            # 检测是否狩猎组群组，并且获取群组信息
            group_info = HunterGroupID.objects.get(groupid=group_id)
            while "" in param_segs:
                param_segs.remove("")
            try:
                optype = param_segs[0].strip()
            except IndexError:
                optype = "help"

            if (optype == "help"):
                msg = "獭獭の狩猎时钟 alpha.1\n/hunt help：帮助\n/hunt check：查询相关\n/hunt kill：设置击杀时间相关\n/hunt edit：手动修改相关\n/hunt list：列出相关\n/hunt maintained：设置为维护后状态（建议维护结束后立即使用）"
            elif (optype == "check"):
                try:
                    monster = param_segs[1].strip()
                    try:
                        # 获取怪物信息
                        monster_info = MonsterList.objects.get(monstername=monster)
                        try:
                            # 获取怪物在各个服务器的击杀时间
                            ktinfo = ServersMonsterKillTime.objects.get(monsterid=monster_info.monsterid)
                            if group_info.servermark == "myc":
                                killtime = ktinfo.myc
                                msg_server = "萌芽池"
                                if ktinfo.mycm == 0:
                                    next_start_time = killtime + monster_info.starttime
                                    next_complete_time = killtime + monster_info.completetime
                                    schedulef = (time.time() - killtime) / monster_info.completetime
                                    schedule = "{:.2%}".format(schedulef)
                                else:
                                    next_start_time = killtime + monster_info.maintainedstarttime
                                    next_complete_time = killtime + monster_info.maintainedcompletetime
                                    schedulef = (time.time() - killtime) / monster_info.maintainedcompletetime
                                    schedule = "{:.2%}".format(schedulef)

                                if monster == "咕尔呱洛斯":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    nct_eorzea_day = getEorzeaDay(next_complete_time)
                                    if nst_eorzea_day < 17:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    getEorzeaMonth(next_start_time) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (17 * 175)
                                    elif nst_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 20:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (17 * 175)
                                    if nct_eorzea_day < 17:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + (getEorzeaMonth(
                                            next_complete_time) * 32 * 24 * 175) + (16 * 24 * 175) + (17 * 175)
                                    elif nct_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_complete_time = next_start_time
                                    elif nct_eorzea_day > 20:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                                            next_complete_time) + 1) * 32 * 24 * 175) + (16 * 24 * 175) + (17 * 175)
                                elif monster == "夺心魔":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    nct_eorzea_day = getEorzeaDay(next_complete_time)
                                    if nst_eorzea_day >= 1 and nst_eorzea_day <= 4:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 4:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175)
                                    if nct_eorzea_day >= 1 and nst_eorzea_day <= 4:
                                        next_complete_time = next_start_time
                                    elif nct_eorzea_day > 4:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                                            next_complete_time) + 1) * 32 * 24 * 175)
                                elif monster == "巨大鳐":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    nct_eorzea_day = getEorzeaDay(next_complete_time)
                                    if nst_eorzea_day < 17:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    getEorzeaMonth(next_start_time) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (12 * 175)
                                    elif nst_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 20:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (12 * 175)
                                    if nct_eorzea_day < 17:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + (getEorzeaMonth(
                                            next_complete_time) * 32 * 24 * 175) + (16 * 24 * 175) + (12 * 175)
                                    elif nct_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_complete_time = next_start_time
                                    elif nct_eorzea_day > 20:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                                            next_complete_time) + 1) * 32 * 24 * 175) + (16 * 24 * 175) + (12 * 175)
                                # 这里全写错了
                                #elif monster == "雷德罗巨蛇":
                                #    try:
                                #        region_to_territory = Territory.objects.get(name=monster_info.region)
                                #        getnstwl = getFollowingWeathers(territory=region_to_territory, cnt=50,
                                #                                        TIMEFORMAT=TIMEFORMAT_YMDHMS,
                                #                                        unixSeconds=next_start_time)
                                #        getnctwl = getFollowingWeathers(territory=region_to_territory, cnt=50,
                                #                                        TIMEFORMAT=TIMEFORMAT_YMDHMS,
                                #                                        unixSeconds=next_complete_time)
                                #        for item in getnstwl:
                                #            if item["pre_name"] == item["name"] and item["name"] == :
                                #                next_start_time = int(time.mktime(time.strptime(item["LT"], TIMEFORMAT_YMDHMS)))
                                #                break
                                #        for item in getnctwl:
                                #            if item["pre_name"] == item["name"]:
                                #                next_complete_time = int(time.mktime(time.strptime(item["LT"], TIMEFORMAT_YMDHMS)))
                                #                break
                                #    except Territory.DoesNotExist:
                                #        msg = "error"
                                #elif monster == "伽洛克":
                                #    try:
                                #        region_to_territory = Territory.objects.get(name=monster_info.region)
                                #        getnstwl = getFollowingWeathers(territory=region_to_territory, cnt=50,
                                #                                        TIMEFORMAT=TIMEFORMAT_YMDHMS,
                                #                                        unixSeconds=next_start_time)
                                #        getnctwl = getFollowingWeathers(territory=region_to_territory, cnt=50,
                                #                                        TIMEFORMAT=TIMEFORMAT_YMDHMS,
                                #                                        unixSeconds=next_complete_time)
                                #        a = 0
                                #        for item in getnstwl:
                                #            if item["pre_name"] == item["name"]:
                                #                a += 1
                                #            if a == 7:
                                #                next_start_time = int(time.mktime(time.strptime(item["LT"], TIMEFORMAT_YMDHMS)))
                                #                break
                                #        for item in getnctwl:
                                #            if item["pre_name"] == item["name"]:
                                #                a += 1
                                #            if a == 1:
                                #                nctag =
                                #            if a == 7:
                                #                next_complete_time = int(time.mktime(time.strptime(item["LT"], TIMEFORMAT_YMDHMS)))

                            elif group_info.servermark == "syzd":
                                killtime = ktinfo.syzd
                                msg_server = "神意之地"
                                if ktinfo.syzdm == 0:
                                    next_start_time = killtime + monster_info.starttime
                                    next_complete_time = killtime + monster_info.completetime
                                    schedulef = (time.time() - killtime) / monster_info.completetime
                                    schedule = "{:.2%}".format(schedulef)
                                else:
                                    next_start_time = killtime + monster_info.maintainedstarttime
                                    next_complete_time = killtime + monster_info.maintainedcompletetime
                                    schedulef = (time.time() - killtime) / monster_info.maintainedcompletetime
                                    schedule = "{:.2%}".format(schedulef)

                                if monster == "咕尔呱洛斯":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    nct_eorzea_day = getEorzeaDay(next_complete_time)
                                    if nst_eorzea_day < 17:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    getEorzeaMonth(next_start_time) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (17 * 175)
                                    elif nst_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 20:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (17 * 175)
                                    if nct_eorzea_day < 17:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + (getEorzeaMonth(
                                            next_complete_time) * 32 * 24 * 175) + (16 * 24 * 175) + (17 * 175)
                                    elif nct_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_complete_time = next_start_time
                                    elif nct_eorzea_day > 20:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                                            next_complete_time) + 1) * 32 * 24 * 175) + (16 * 24 * 175) + (17 * 175)
                                elif monster == "夺心魔":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    nct_eorzea_day = getEorzeaDay(next_complete_time)
                                    if nst_eorzea_day >= 1 and nst_eorzea_day <= 4:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 4:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175)
                                    if nct_eorzea_day >= 1 and nst_eorzea_day <= 4:
                                        next_complete_time = next_start_time
                                    elif nct_eorzea_day > 4:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                                            next_complete_time) + 1) * 32 * 24 * 175)
                                elif monster == "巨大鳐":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    nct_eorzea_day = getEorzeaDay(next_complete_time)
                                    if nst_eorzea_day < 17:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    getEorzeaMonth(next_start_time) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (12 * 175)
                                    elif nst_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 20:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (12 * 175)
                                    if nct_eorzea_day < 17:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + (getEorzeaMonth(
                                            next_complete_time) * 32 * 24 * 175) + (16 * 24 * 175) + (12 * 175)
                                    elif nct_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_complete_time = next_start_time
                                    elif nct_eorzea_day > 20:
                                        next_complete_time = (getEorzeaYear(
                                            next_complete_time) * 12 * 32 * 24 * 175) + ((getEorzeaMonth(
                                            next_complete_time) + 1) * 32 * 24 * 175) + (16 * 24 * 175) + (12 * 175)

                            msg = monster_info.region + " " + monster_info.monstername + " " + msg_server + "\n进度：" + schedule + "\n上次击杀时间：" + time.strftime(TIMEFORMAT_MDHMS, time.localtime(killtime)) + "\n开始触发时间：" + time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_start_time)) + "\n必定触发时间：" + time.strftime(TIMEFORMAT_MDHMS, time.localtime(next_complete_time)) + "\n触发方法：" + monster_info.triggermethod

                        except ServersMonsterKillTime.DoesNotExist:
                            msg = "[error]"
                    except MonsterList.DoesNotExist:
                        msg = "目前只支持S级狩猎怪查询（需要全称）"
                except IndexError:
                    msg = "狩猎时钟check命令示例：\n/hunt check [怪物名称]\n查询怪物的击杀时间、触发时间、触发说明等信息\n注：触发时间已经计算好触发条件的日期和天气等条件"

            elif (optype == "kill"):
                try:
                    monster = param_segs[1].strip()
                    try:
                        monster_info = MonsterList.objects.get(monstername=monster)
                        try:
                            ktinfo = ServersMonsterKillTime.objects.get(monsterid=monster_info.monsterid)
                            if group_info.servermark == "myc":
                                ktinfo.myc = time.time()
                                ktinfo.mycm = 0
                                ktinfo.save()
                                msg_server = "萌芽池"
                            elif group_info.servermark == "syzd":
                                ktinfo.syzd = time.time()
                                ktinfo.syzdm = 0
                                ktinfo.save()
                                msg_server = "神意之地"

                            msg = msg_server + "的" + monster_info.monstername + "击杀时间已记录"
                        except ServersMonsterKillTime.DoesNotExist:
                            msg = "[error]"
                    except MonsterList.DoesNotExist:
                        msg = "目前只支持S级狩猎怪"
                except IndexError:
                    msg = "狩猎时钟list命令示例：\n/hunt kill [怪物名称]\n设置怪物的击杀时间为现在"

            elif (optype == "list"):
                try:
                    setype = param_segs[1].strip()
                    if setype == "cd":
                        a = 1
                        msg = "可以触发的S怪：\n"
                        cdlist = []
                        qcdlist = []
                        if group_info.servermark == "myc":
                            while a < 30:
                                ktinfo = ServersMonsterKillTime.objects.get(monsterid=a)
                                monster_info = MonsterList.objects.get(monsterid=a)
                                killtime = ktinfo.myc
                                if ktinfo.mycm == 0:
                                    next_start_time = killtime + monster_info.starttime
                                    schedulef = (time.time() - killtime) / monster_info.completetime
                                    schedule = "{:.2%}".format(schedulef)
                                else:
                                    next_start_time = killtime + monster_info.maintainedstarttime
                                    schedulef = (time.time() - killtime) / monster_info.maintainedcompletetime
                                    schedule = "{:.2%}".format(schedulef)
                                if monster_info.monstername == "咕尔呱洛斯":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    if nst_eorzea_day < 17:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    getEorzeaMonth(next_start_time) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (17 * 175)
                                    elif nst_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 20:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (17 * 175)
                                elif monster_info.monstername == "夺心魔":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    if nst_eorzea_day >= 1 and nst_eorzea_day <= 4:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 4:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175)
                                elif monster_info.monstername == "巨大鳐":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    if nst_eorzea_day < 17:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    getEorzeaMonth(next_start_time) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (12 * 175)
                                    elif nst_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 20:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (12 * 175)
                                if next_start_time <= time.time():
                                    cdlist.append(
                                        monster_info.region + " " + monster_info.monstername + " " + schedule + "\n" + time.strftime(
                                            TIMEFORMAT_MDHMS, time.localtime(next_start_time)))
                                elif next_start_time - 3600 < time.time() and next_start_time > time.time():
                                    qcdlist.append(
                                        monster_info.region + " " + monster_info.monstername + " " + schedule + "\n" + time.strftime(
                                            TIMEFORMAT_MDHMS, time.localtime(next_start_time)))
                                a += 1
                        if group_info.servermark == "syzd":
                            while a < 30:
                                ktinfo = ServersMonsterKillTime.objects.get(monsterid=a)
                                monster_info = MonsterList.objects.get(monsterid=a)
                                killtime = ktinfo.syzd
                                if ktinfo.syzdm == 0:
                                    next_start_time = killtime + monster_info.starttime
                                    schedulef = (time.time() - killtime) / monster_info.completetime
                                    schedule = "{:.2%}".format(schedulef)
                                else:
                                    next_start_time = killtime + monster_info.maintainedstarttime
                                    schedulef = (time.time() - killtime) / monster_info.completetime
                                    schedule = "{:.2%}".format(schedulef)
                                if monster_info.monstername == "咕尔呱洛斯":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    if nst_eorzea_day < 17:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    getEorzeaMonth(next_start_time) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (17 * 175)
                                    elif nst_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 20:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (17 * 175)
                                elif monster_info.monstername == "夺心魔":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    if nst_eorzea_day >= 1 and nst_eorzea_day <= 4:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 4:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175)
                                elif monster_info.monstername == "巨大鳐":
                                    nst_eorzea_day = getEorzeaDay(next_start_time)
                                    if nst_eorzea_day < 17:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    getEorzeaMonth(next_start_time) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (12 * 175)
                                    elif nst_eorzea_day >= 17 and nst_eorzea_day <= 20:
                                        next_start_time = next_start_time
                                    elif nst_eorzea_day > 20:
                                        next_start_time = (getEorzeaYear(next_start_time) * 12 * 32 * 24 * 175) + (
                                                    (getEorzeaMonth(next_start_time) + 1) * 32 * 24 * 175) + (
                                                                      16 * 24 * 175) + (12 * 175)
                                if next_start_time <= time.time():
                                    cdlist.append(
                                        monster_info.region + " " + monster_info.monstername + " " + schedule + "\n" + time.strftime(
                                            TIMEFORMAT_MDHMS, time.localtime(next_start_time)))
                                elif next_start_time - 3600 < time.time() and next_start_time > time.time():
                                    qcdlist.append(
                                        monster_info.region + " " + monster_info.monstername + " " + schedule + "\n" + time.strftime(
                                            TIMEFORMAT_MDHMS, time.localtime(next_start_time)))
                                a += 1
                        for cdmsg in cdlist:
                            msg += "{}\n".format(cdmsg)
                        if len(qcdlist) > 0:
                            msg += "\n准备进入触发时间的S怪（1小时内）：\n"
                            for qcdmsg in qcdlist:
                                msg += "{}\n".format(qcdmsg)

                except IndexError:
                    msg = "狩猎时钟list命令示例：\n/hunt list [选项]\n选项解释：\ncd：列出可触发的s"
                          # "和其开始时间、必定触发时间、进度\n50s：列出所有2.0的s怪和其开始时间\n60s：列出所有3.0的s怪和其开始时间\n70s：列出所有4.0的s怪和其开始时间"

            elif (optype == "maintained"):
                try:
                    a = 1
                    if group_info.servermark == "myc":
                        while a < 30:
                            ktinfo = ServersMonsterKillTime.objects.get(monsterid=a)
                            ktinfo.myc = time.time()
                            ktinfo.mycm = 1
                            ktinfo.save()
                            a += 1
                    elif group_info.servermark == "syzd":
                        while a < 30:
                            ktinfo = ServersMonsterKillTime.objects.get(monsterid=a)
                            ktinfo.syzd = time.time()
                            ktinfo.syzdm = 1
                            ktinfo.save()
                            a += 1
                    msg = "击杀时间已设置为当前时间，并修改触发时长为维护后触发时长"
                except ServersMonsterKillTime.DoesNotExist:
                    msg = ""

            elif (optype == "edit"):
                try:
                    monster = param_segs[1].strip()
                    YMD = param_segs[2].strip()
                    HMS = param_segs[3].strip()
                    try:
                        monster_info = MonsterList.objects.get(monstername=monster)
                        try:
                            ktinfo = ServersMonsterKillTime.objects.get(monsterid=monster_info.monsterid)
                            edittimestr = YMD + " " + HMS
                            edittime = int(time.mktime(time.strptime(edittimestr, TIMEFORMAT_YMDHMS)))
                            if group_info.servermark == "myc":
                                ktinfo.myc = edittime
                                ktinfo.save()
                            elif group_info.servermark == "syzd":
                                ktinfo.syzd = edittime
                                ktinfo.save()
                            msg = monster_info.monstername + "的击杀时间已修改为：\n" + edittimestr
                        except ServersMonsterKillTime.DoesNotExist:
                            msg = "[error]"
                    except MonsterList.DoesNotExist:
                        msg = "目前只支持S级狩猎怪"
                except IndexError:
                    msg = "狩猎时钟edit命令示例：\n/hunt edit [怪物名称] [时间]\n时间格式例：\n2019-07-22 02:44:45"

        except HunterGroupID.DoesNotExist:
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

