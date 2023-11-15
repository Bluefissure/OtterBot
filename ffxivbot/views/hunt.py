from ast import operator
import os
import time
import json
import functools
import operator
from datetime import datetime
from zoneinfo import ZoneInfo
from django.http import JsonResponse, HttpResponseRedirect
from django.utils.timezone import make_aware
from django.contrib.auth.decorators import login_required
from django.db.models import Q, Max, F, Case, Value, When
from ffxivbot.models import BannedCharacter, Monster, HuntLog, HuntGroup, Server
from authlib.integrations.requests_client import OAuth2Session
from .ren2res import ren2res
import traceback

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FFXIVBOT_ROOT = os.environ.get("FFXIVBOT_ROOT", BASE_DIR)
CONFIG_PATH = os.environ.get(
    "FFXIVBOT_CONFIG", os.path.join(FFXIVBOT_ROOT, "ffxivbot/config.json")
)
XIVID_API_BASE = "https://api.xivid.cc/v1"

def get_hms(seconds):
    seconds = abs(int(seconds))
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    return h, m, s

def gen_hunts(user, sonar=False, bird=False):
    hunt_list = []
    resource_groups = set()
    is_relay = sonar or bird
    sources = []
    if not is_relay:
        latest_kill_logs = HuntLog.objects.filter(
            Q(hunt_group__group__member_list__contains=user.user_id, log_type='kill') | Q(hunt_group__public=True) | Q(log_type="manual")
        ).values('server__name', 'monster', 'hunt_group', 'instance_id').annotate(Max('time'))
    else:
        conditions = [Q(log_type='manual')]
        if sonar:
            conditions.append(Q(log_type='sonar'))
            sources.append('Sonar')
        if bird:
            conditions.append(Q(log_type='bird'))
            sources.append('银山雀')
        latest_kill_logs = HuntLog.objects.filter(functools.reduce(operator.__or__, conditions), time__gt=time.time()-3600*24*7*2)\
            .annotate(instanced_id=Case(
                When(instance_id=0, then=Value(1)),
                default=F('instance_id'),
                ))\
            .values('server__name', 'monster', 'instanced_id').annotate(Max('time'))

    # print(f"#latest_kill_logs:{latest_kill_logs.count()}")
    maintain_logs = HuntLog.objects.filter(log_type='maintain').values('server__name').annotate(Max('time'))
    server_maintains = {}
    for log in maintain_logs:
        server_maintains[log['server__name']] = log['time__max']
    monster_dict = {}
    for monster in Monster.objects.all():
        monster_dict[monster.id] = monster
    for latest_kill_log in latest_kill_logs:
        try:
            if not is_relay:
                hunt_group = HuntGroup.objects.get(id=latest_kill_log['hunt_group'])
            else:
                hunt_group = ', '.join(sources)
            latest_kill_log['instance_id'] = latest_kill_log.get('instance_id', latest_kill_log.get('instanced_id', 0))
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
            spawn_deltaf = (time.time() - next_spawn_time)
            spawn_percentf = (time.time() - next_spawn_time) / (pop_cooldown - spawn_cooldown)
            cd_schedule = "{:.2%}".format(cd_schedulef)
            schedule = "{:.2%}".format(schedulef)
            spawn_percent = "{:.2%}".format(spawn_percentf)
            h, m, s = get_hms(spawn_deltaf)
            spawn_delta = f'-{h:d}:{m:02d}:{s:02d}'
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
            monster_info["spawn_percentf"] = spawn_percentf
            monster_info["spawn_percent"] = spawn_percent
            monster_info["schedulef"] = schedulef
            monster_info["schedule"] = schedule
            monster_info["spawn_deltaf"] = spawn_deltaf
            monster_info["spawn_delta"] = spawn_delta
            monster_info["in_cd"] = in_cd
            monster_info["kill_timestamp"] = kill_time
            monster_info["next_spawn_timestamp"] = next_spawn_time
            monster_info["next_pop_timestamp"] = next_pop_time
            monster_info["info"] = monster.info
            monster_info["resource"] = str(hunt_group)
            hunt_list.append(monster_info)
        except Exception as e:
            traceback.print_exc()
    return hunt_list, resource_groups

def check_manual_upload(qquser) -> bool:
    if not qquser.can_manual_upload_hunt:
        return False
    char_list = json.loads(qquser.xivid_character).get("data", [])
    if len(char_list) == 0:
        return False
    return True

def handle_hunt_revoke(req):
    qquser = req.user.qquser
    try:
        latest_log = qquser.upload_hunt_log.latest('id')
        latest_log.delete()
        time_str = datetime.fromtimestamp(latest_log.time).strftime("%Y-%m-%d %H:%M:%S") + '(北京时间)'
        succ_msg = f"记录 {latest_log.monster.cn_name} {latest_log.server.name} {time_str} 已撤回。"
    except HuntLog.DoesNotExist:
        return JsonResponse({
            "response": "error",
            "message": "没有可撤回的记录。",
        })
    return JsonResponse({
        "response": "success",
        "message": succ_msg,
    })
    
def handle_hunt_post(req):
    json_req = json.loads(req.body)
    if json_req.get('optype') == 'revoke_manual_upload':
        return handle_hunt_revoke(req)
    if json_req.get('optype') != 'manual_upload_hunt':
        return JsonResponse({'response': 'error', 'message': 'API optype error'})
    if not (json_req["monster_name"] and json_req["server_name"] and json_req["time"]):
        return JsonResponse({'response': 'error', 'message': 'API parameter error'})
    monster = Monster.objects.get(cn_name=json_req["monster_name"])
    server = Server.objects.get(name=json_req["server_name"])
    timestamp = int(json_req["time"])
    if timestamp > time.time():
        return JsonResponse({'response': 'error', 'message': '时间不能大于当前时间（请按照本地时间填写）。'})

    if not req.user.qquser.can_manual_upload_hunt:
        return JsonResponse({
            "response": "error",
            "message": "No privilege to upload hunt log.",
        })
    with open(CONFIG_PATH, "r") as f:
        config = json.load(f)
        XIVID_CLIENT_ID = os.environ.get("XIVID_CLIENT_ID", config.get("XIVID_CLIENT_ID"))
        XIVID_KEY = os.environ.get("XIVID_KEY", config.get("XIVID_KEY"))
    token = json.loads(req.user.qquser.xivid_token)
    token_endpoint = XIVID_API_BASE + "/oauth/token"
    client = OAuth2Session(XIVID_CLIENT_ID, XIVID_KEY, token=token, token_endpoint=token_endpoint)
    res = client.get(XIVID_API_BASE + "/character")
    res_json = res.json()
    if res_json["code"] != 200:
        return JsonResponse({
            "response": "error",
            "message": f"Xivid API error: {res_json['message']}",
        })
    char_list = res_json["data"]
    if len(char_list) == 0:
        return JsonResponse({
            "response": "error",
            "message": "No character found.",
        })
    req.user.qquser.xivid_character = json.dumps({"data": char_list})
    req.user.qquser.xivid_token = json.dumps(client.token)
    req.user.qquser.save()
    character_list = []
    banned = False
    for char in char_list:
        if BannedCharacter.objects.filter(xivid_id=int(char["id"])).exists():
            banned = True
            break
        character_list.append(f"{char['id']}:{char['name']}({char['worldId']})")
    if banned:
        return JsonResponse({
            "response": "error",
            "message": "Character is banned.",
        })
    character_list_str = ', '.join(character_list)
    hunt_log = HuntLog(
        monster=monster,
        server=server,
        log_type="manual",
        time=timestamp,
        uploader=req.user.qquser,
        uploader_char=character_list_str,
    )
    if json_req["monster_name"].endswith('1'):
        hunt_log.instance_id = 1
    elif json_req["monster_name"].endswith('2'):
        hunt_log.instance_id = 2
    elif json_req["monster_name"].endswith('3'):
        hunt_log.instance_id = 3
    else:
        monster_name2 = json_req["monster_name"] + '2'
        if Monster.objects.filter(cn_name=monster_name2).exists():
            hunt_log.instance_id = 1
    # from django.core import serializers
    # serialized_obj = serializers.serialize('json', [ hunt_log, ])
    # print(serialized_obj)
    hunt_log.save()
    time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") + '(北京时间)'
    succ_msg = f"{hunt_log.monster.cn_name} {hunt_log.server.name} {time_str} 已记录。"
    return JsonResponse({
        "response": "success",
        "message": succ_msg,
    })

@login_required(login_url='/login/')
def hunt(req):
    if req.method == 'GET':
        hunt_list, resource_groups = gen_hunts(req.user.qquser, False)
        monster_list = sorted([x['cn_name'] for x in Monster.objects.all().values('cn_name')])
        server_list = [x['name'] for x in Server.objects.all().values('name')]
        can_manual_upload = check_manual_upload(req.user.qquser)
        return ren2res('hunt.html', req, {
            "hunt_list": hunt_list,
            "monster_list": monster_list,
            "server_list": server_list,
            "can_manual_upload": can_manual_upload,
            "resources": ", ".join(list(resource_groups)),
        })
    try:
        response = handle_hunt_post(req)
    except:
        return JsonResponse({
            "response": "error",
            "message": "Server error, please contact admin.",
        })
    return response

#@login_required(login_url='/login/')
def hunt_relay(req, sonar=True, bird=True):
    if req.method == 'GET':
        hunt_list, resource_groups = gen_hunts(None, sonar=sonar, bird=bird)
        monster_list = sorted([x['cn_name'] for x in Monster.objects.all().values('cn_name')])
        server_list = [x['name'] for x in Server.objects.all().values('name')]
        can_manual_upload = check_manual_upload(req.user.qquser) if not req.user.is_anonymous else False
        return ren2res('hunt.html', req, {
            "hunt_list": hunt_list,
            "monster_list": monster_list,
            "server_list": server_list,
            "can_manual_upload": can_manual_upload,
            "resources": ", ".join(list(resource_groups)),
        })
    response = handle_hunt_post(req)
    return response

def hunt_sonar(req):
    return hunt_relay(req, sonar=True, bird=False)

def hunt_bird(req):
    return hunt_relay(req, sonar=False, bird=True)

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


# Helper functions to calculate special conditions
