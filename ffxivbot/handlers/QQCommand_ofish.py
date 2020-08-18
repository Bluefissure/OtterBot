from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import time
import datetime
import math

# fmt: off
pattern =  [1,4,2,5,3,6,1,4,2,5,3,6,
            4,1,5,2,6,3,4,1,5,2,6,3,
            2,5,3,6,1,4,2,5,3,6,1,4,
            5,2,6,3,4,1,5,2,6,3,4,1,
            3,6,1,4,2,5,3,6,1,4,2,5,
            6,3,4,1,5,2,6,3,4,1,5,2]
# fmt: on
routeName = ["梅尔夜晚", "梅尔白天", "梅尔黄昏", "罗塔夜晚", "罗塔白天", "罗塔黄昏"]
routeComment = [
    "海龙成就 + ※珊瑚蝠鲼",
    "章鱼成就",
    "※索蒂斯 + ※依拉丝莫龙",
    "※索蒂斯 + ※石骨鱼",
    "水母成就 + 冲分推荐",
    "鲨鱼成就 + ※珊瑚蝠鲼",
]
routeComment2 = ["", "1区可冲分,追梦失败转成就车", "1区可以冲水母成就", "2区可以冲海龙成就", "", "可以和鲨鱼队一起冲分"]
schedules = [
    "梅尔托尔海峡南(夜)-加拉迪翁湾外海(日)-梅尔托尔海峡北(夕)",
    "梅尔托尔海峡南(日)-加拉迪翁湾外海(夕)- 梅尔托尔海峡北(夜)",
    "梅尔托尔海峡南(夕)-加拉迪翁湾外海(夜)- 梅尔托尔海峡北(日)",
    "加拉迪翁湾外海(夜)-梅尔托尔海峡南(日)- 罗塔诺海海面(夕)",
    "加拉迪翁湾外海(日)-梅尔托尔海峡南(夕)- 罗塔诺海海面(夜)",
    "加拉迪翁湾外海(夕)-梅尔托尔海峡南(夜)- 罗塔诺海海面(日)",
]

# Modified from http://fish.senriakane.com/ocean.html
def QQCommand_ofish(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        command = receive["message"].replace("/ofish", "").strip()
        if (not command) or command.isdigit():
            command = "3" if not command else command
            count = int(command)
            count = min(count, 5)
            # fmt: on
            offset = 20
            date = datetime.datetime.now()
            last_time = datetime.datetime.now().strftime("%Y-%m-%d 22:15:00")
            if str(date) < str(last_time):
                t = (date - datetime.timedelta(days=1)).strftime("%Y-%m-%d 16:00:00")
            else:
                t = date.strftime("%Y-%m-%d 16:00:00")
            ts = int(time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S")))
            selectedTwoHourChunk = math.floor(ts / (60 * 60 * 2))
            tempTime = (selectedTwoHourChunk + offset) % 72
            i = 0
            num = 0
            route = ""
            rName = []
            while i < 12:
                if tempTime + i >= 72:
                    temp = tempTime + i - 72
                else:
                    temp = tempTime + i
                temppoop = datetime.datetime.fromtimestamp(
                    (selectedTwoHourChunk + i + 4) * (60 * 60 * 2)
                )
                i += 1
                if str(date) < str(temppoop.strftime("%Y-%m-%d %H:15")) and num < count:
                    route += (
                        "时间："
                        + temppoop.strftime("%Y-%m-%d %H:%M")
                        + "--航线："
                        + routeName[pattern[temp] - 1]
                        + "\n说明："
                        + routeComment[pattern[temp] - 1]
                        + "     备注："
                        + routeComment2[pattern[temp] - 1]
                        + "\n行程："
                        + schedules[pattern[temp] - 1]
                        + "\n"
                    )
                    rName.append(routeName[pattern[temp] - 1])
                    route += "\n"
                    num += 1
            first_time = datetime.datetime.now().strftime("%Y-%m-%d 18:15:00")
            if str(date) > str(first_time) or count > num:
                t = date.strftime("%Y-%m-%d 16:00:00")
                ts = int(time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S")))
                selectedTwoHourChunk = math.floor(ts / (60 * 60 * 2))
                tempTime = (selectedTwoHourChunk + offset) % 72
                i = 0
                while i < 12:
                    if tempTime + i >= 72:
                        temp = tempTime + i - 72
                    else:
                        temp = tempTime + i
                    temppoop = datetime.datetime.fromtimestamp(
                        (selectedTwoHourChunk + i + 4) * (60 * 60 * 2)
                    )
                    i += 1
                    if num < count:
                        route += (
                            "时间："
                            + temppoop.strftime("%Y-%m-%d %H:%M")
                            + "--航线："
                            + routeName[pattern[temp] - 1]
                            + "\n说明："
                            + routeComment[pattern[temp] - 1]
                            + "     备注："
                            + routeComment2[pattern[temp] - 1]
                            + "\n行程："
                            + schedules[pattern[temp] - 1]
                            + "\n"
                        )
                        rName.append(routeName[pattern[temp] - 1])
                        route += "\n"
                        num += 1
            last_msg = route[:-1].strip()
            msg = last_msg
        elif command.startswith("海龙成就"):
            rN = 1
            pQ = 3
            text = "梅尔托尔海峡北晚班（海龙成就 + ※珊瑚蝠鲼）"
            msg = extract_route(rN, pQ, text)
            msg += "\n查宏前面加个宏字，e.g./ofish 宏xx成就"
        elif command.startswith("海马成就"):
            rN = 1
            pQ = 3
            text = "梅尔托尔海峡北晚班（海龙成就 + ※珊瑚蝠鲼）"
            msg = extract_route(rN, pQ, text)
            msg += "\n查宏前面加个宏字，e.g./ofish 宏xx成就"
        elif command.startswith("章鱼成就"):
            rN = 2
            pQ = 3
            text = "梅尔托尔海峡北早班（章鱼成就）"
            msg = extract_route(rN, pQ, text)
            msg += "\n查宏前面加个宏字，e.g./ofish 宏xx成就"
        elif command.startswith("依拉丝莫龙"):
            rN = 3
            pQ = 3
            text = "梅尔托尔海峡北午班（※索蒂斯 + ※依拉丝莫龙）"
            msg = extract_route(rN, pQ, text)
        elif command.startswith("石骨鱼"):
            rN = 4
            pQ = 3
            text = "罗塔诺海海面晚班　（※索蒂斯 + ※石骨鱼）"
            msg = extract_route(rN, pQ, text)
        elif command.startswith("水母成就"):
            rN = 5
            pQ = 3
            text = "罗塔诺海海面早班　（水母成就 + 冲分推荐）"
            msg = extract_route(rN, pQ, text)
            msg += "\n查宏前面加个宏字，e.g./ofish 宏xx成就"
        elif command.startswith("鲨鱼成就"):
            rN = 6
            pQ = 3
            text = "罗塔诺海海面午班　（鲨鱼成就 + ※珊瑚蝠鲼）"
            msg = extract_route(rN, pQ, text)
            msg += "\n查宏前面加个宏字，e.g./ofish 宏xx成就"
        elif command.startswith("珊瑚蝠鲼"):
            rN = 1
            pQ = 2
            text = "梅尔托尔海峡北晚班（海龙成就 + ※珊瑚蝠鲼）"
            msg = extract_route(rN, pQ, text)
            rN = 6
            pQ = 2
            text = "罗塔诺海海面午班　（鲨鱼成就 + ※珊瑚蝠鲼）"
            msg += "\n" + extract_route(rN, pQ, text)
        elif command.startswith("索蒂斯"):
            rN = 3
            pQ = 2
            text = "梅尔托尔海峡北午班（※索蒂斯 + ※依拉丝莫龙）"
            msg = extract_route(rN, pQ, text)
            rN = 4
            pQ = 2
            text = "罗塔诺海海面晚班　（※索蒂斯 + ※石骨鱼）"
            msg += "\n" + extract_route(rN, pQ, text)
        elif command.startswith("加拉迪翁湾外海幻海流"):
            # from https://bbs.nga.cn/read.php?tid=20553241
            msg = """索蒂斯
捕鱼人之识触发条件：钓起2*天堂之钥+1*海神印
我觉得好像没什么必要用专一，除非你真的只想要它。
(海面上闪耀着星辰般的神秘光辉！星辰般的神秘光辉不见了……)
时长15s，要求时间“夜晚”，用火 萤 没想到吧"""
        elif command.startswith("梅尔托尔海峡南幻海流"):
            msg = """珊瑚蝠鲼
捕鱼人之识触发条件：钓起2*巨大枪鱼
以小钓大，双提中杆[!!]，可能会歪。
(海底有像是珊瑚的东西在动！像是珊瑚的东西不见了……)
时长15s，要求时间“夜晚”，用小 虾 肉 笼 没想到吧"""
        elif command.startswith("梅尔托尔海峡北幻海流"):
            msg = """依拉丝莫龙
捕鱼人之识触发条件：钓起3*守领鳍龙
直接双提鱼王杆[!!!]
(海里有已灭绝生物的身影！已灭绝生物的身影不见了……)
时长15s，要求时间“白天”，用重 铁 板 钩 没想到吧"""
        elif command.startswith("罗塔诺海海面幻海流"):
            msg = """石骨鱼
捕鱼人之识触发条件：钓起1*深海鳗+1*沉寂者
随便提基本没问题
(海底有像是石块的东西在动！像是石块的东西不见了……)
时长15s，要求时间“黄昏”，用沟 鼠 尾 巴 没想到吧"""
        elif command.startswith("加拉迪翁湾外海"):
            msg = """醉鱼
捕鱼人之识触发条件：钓起3*加拉迪翁鳀鱼
钓门票建议磷虾，因为这货经常不咬钩，轻杆[!]分不开，中间乱入幻海流什么的，如果你冲着它去，可以专一垂钓+双重提钩。
(看到了一个像是鲁加族的男性！像是鲁加族的男性不见了……)
时长1分钟，用磷虾"""
        elif command.startswith("梅尔托尔海峡南"):
            msg = """强烈警告，鱼王杆[!!!]大部分是莫莫拉·莫拉，如果你觉得是触发鱼记得精准提钩。
小利维亚桑
捕鱼人之识触发条件：钓起1*步兵剑
钓门票建议磷虾，短中杆[!!]很好认。微风和强风天气不会出现，另有世界第一干扰鱼莫莫拉·莫拉爱你
(像是利维亚桑的身影从船下掠过！像是利维亚桑的身影不见了……)
时长1分钟，用刺螠"""
        elif command.startswith("梅尔托尔海峡北"):
            msg = """这个海域里的鱼王杆[!!!]全部是精准提钩。
海流星
捕鱼人之识触发条件：钓起1*古老恐鱼
钓门票建议石沙蚕，中时长轻杆[!]
(像是流星一般的赤红色光芒从船下掠过！像是流星一般的赤红色光芒不见了……)
时长1分钟，用石沙蚕，精准提钩"""
        elif command.startswith("罗塔诺海海面"):
            msg = """海铠靴
捕鱼人之识触发条件：钓起2*深红钓鮟鱇
门票用刺螠钓，中等时长的中杆[!!]，实在不行可以开个专一
(海里有像是甲胄反射的暗淡光辉！像是甲胄反射的暗淡光辉不见了……)
时长1分钟，用磷虾"""
        elif command.startswith("宏鲨鱼成就"):
            msg = """---钓场一：加拉迪翁湾外海-黄昏---
暴雨天气直接跳船。
刺螠[!!!]→暗淡鲨，满GP可以开个专一，可能会歪到幻光巨齿鲨。满了还没遇到鲨鱼可以适当撒饵。
幻海流中用刺螠，双提[!!!]→漏斗鲨*4/3-4s[!!]→幽灵鲨*4，平提5-6s[!!]→流银刃
——————————————————————————————
---钓场二：梅尔托尔海峡南-夜晚---
恢复GP，随便钓，可以用磷虾触发一下幻海
——————————————————————————————
---钓场三：罗塔诺海海面-白天---
刺螠，双提24s前[!!!]→铬铁锤头鲨*4，24s后平提专一再双提，可能会歪到幻光鲈。
幻海流中用刺螠，双提[!!!]→处刑者*4，平提[!!]→清道夫
推荐连招：双重提钩-专一垂钓-双重提钩"""
        elif command.startswith("宏章鱼成就"):
            msg = """---钓场一：梅尔托尔海峡南-白天---
保存GP，随便钓
——————————————————————————————
---钓场二：加拉迪翁湾外海-黄昏---
磷虾，18s+[!!]→青色章鱼*4，阴云、薄雾18s即可双提，小雨、暴雨24s再双提，其他情况平提专一再双提
幻海流中用磷虾，双提0-2.8s[!!]→人鱼发*4，2.8s以上平提
——————————————————————————————
---钓场三：梅尔托尔海峡北-夜晚---
石沙蚕[!!!]精准提钩→幻光海马 触发幻海流
幻海流中用磷虾，双提5s+[!!]→幻纱披风*4
推荐连招：双重提钩-专一垂钓-双重提钩"""
        elif command.startswith("宏海马成就"):
            msg = """---钓场一：梅尔托尔海峡南-夜晚---
薄雾、阴云天气直接跳船。
石沙蚕，8s-16s的[!]→蓬松海龙，12s以上可以酌情双提
如果触发了幻海流(不触发最好)，就用刺螠[!]→高级以太药虱 以小钓大4-5s[!!]→以太海龙
——————————————————————————————
---钓场二：加拉迪翁湾外海-白天---
恢复GP，随便钓
——————————————————————————————
---钓场三：梅尔托尔海峡北-黄昏---
石沙蚕[!!!]精准提钩→幻光海马 触发幻海流，幻海流中双提5s以上的[!]→珊瑚海龙*4
推荐连招：双重提钩-专一垂钓-双重提钩"""
        elif command.startswith("宏水母成就"):
            msg = """石沙蚕，认准4s[!]→拉诺西亚水母，自信双提
建议使用宏：
/ac 抛竿
/wait 4
/ac 双重提钩
/ac 提钩
第一个点钓完报数，不够就跳"""
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, last_msg))
        logging.error(e)
    return action_list


def extract_route(rN: int, pQ: int, text: str):
    try:
        date = datetime.datetime.now()
        t = date.strftime("%Y-%m-%d 16:00:00")
        ts = int(time.mktime(time.strptime(t, "%Y-%m-%d %H:%M:%S")))
        currentTwoHourChunks = math.floor(ts / (60 * 60 * 2))
        offset = 16
        temptime = currentTwoHourChunks % 72
        tries = 0
        matches = 0
        matchesTimes = []

        while matches < pQ and tries < pQ * 20:
            temp = currentTwoHourChunks + tries + offset
            if pattern[(temp % 72)] == rN:
                matchesTimes.append(temp)
                matches += 1
            tries += 1

        i = 0
        temptext = ""
        while i < len(matchesTimes):
            temppoop = datetime.datetime.fromtimestamp(
                (matchesTimes[i] - offset) * (60 * 60 * 2)
            )
            temptext += temppoop.strftime("%Y-%m-%d %H:%M") + "  " + text + "\n"
            i += 1
            msg = temptext[:-1]
    except Exception as e:
        msg = "Error: {}".format(type(e))
    return msg
