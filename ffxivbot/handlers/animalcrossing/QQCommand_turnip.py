import sys
import os
from ..QQEventHandler import QQEventHandler
from ..QQUtils import *
from .Turnip import Turnip
from ffxivbot.models import *
import logging
import re
import traceback
import time
from datetime import datetime, timedelta
from django.db.models import Q
from pytz import timezone, UnknownTimeZoneError

ONE_DAY = 24 * 3600

def get_week_start(user):
    t = datetime.now(timezone(user.timezone))
    t -= timedelta(hours=t.hour, minutes=t.minute, seconds=t.second)
    while t.weekday() != 6:
        t -= timedelta(days=1)
    return t.timestamp()

def get_price_info(user):
    week_start_time = get_week_start(user)
    price_list = []
    price_msg = ""
    prices = TurnipPrice.objects.filter(Q(time__gte=week_start_time) & Q(time__lte=week_start_time + ONE_DAY),user=user)
    price_list.append(prices[0].price if prices else -1)
    cur_time = week_start_time + ONE_DAY
    i2s = lambda x: str(x) if x > 0 else "-"
    # print("Weekday#0 am:{}".format(week_start_time))
    for _ in range(6):
        # print("Weekday#{} am:{} pm:{}".format(_+1, cur_time, cur_time + ONE_DAY/2))
        prices = TurnipPrice.objects.filter(Q(time__gte=cur_time) & Q(time__lt=cur_time + ONE_DAY/2),user=user)
        price_list.append(prices[0].price if prices else -1)
        prices = TurnipPrice.objects.filter(Q(time__gte=cur_time + ONE_DAY/2) & Q(time__lt=cur_time + ONE_DAY),user=user)
        price_list.append(prices[0].price if prices else -1)
        cur_time += ONE_DAY
    for i, price in enumerate(price_list):
        price_msg += i2s(price) if i == 0 else (
            ("/"+i2s(price)) if i % 2 == 0 else (" "+i2s(price))
        )
    # print("price_msg:{}".format(price_msg))
    return price_list, price_msg


def is_integer(n):
    try:
        float(n)
    except ValueError:
        return False
    else:
        return float(n).is_integer()


def QQCommand_turnip(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        action_list = []
        receive = kwargs["receive"]
        bot = kwargs["bot"]
        user_id = receive["user_id"]
        (qquser, _) = QQUser.objects.get_or_create(
            user_id=user_id
        )
        msg = "turnip testing"
        para_segs = receive["message"].replace("/turnip","",1).split(" ")
        while "" in para_segs:
            para_segs.remove("")
        para_segs = list(map(lambda x:x.strip(), para_segs))
        weekday_str = ["日", "一", "二", "三", "四", "五", "六"]
        am_pm_str = {
            "am":"上午",
            "pm":"下午"
        }
        if len(para_segs) == 0 or para_segs[0] == "help":
            msg = '''动物森友会獭头菜价格趋势模型
/turnip timezone $timezone: 设置动森的时区为$timezone（默认北京时间）
/turnip price $price: 记录当前当前买入/收购大头菜价格为$price
/turnip predict: 预测大头菜的价格曲线
/turnip predict $price_list: 按照$price_list预测大头菜的价格曲线
/turnip info: 查看本周记录的大头菜价格
/turnip algorithm: 所使用的算法
/turnip about: 所抄代码的项目
'''
        else:
            if para_segs[0] == "timezone":
                try:
                    timezone(para_segs[1])
                    qquser.timezone = para_segs[1]
                    qquser.save(update_fields=["timezone"])
                    msg = "时区已被设定为{}".format(qquser.timezone)
                except UnknownTimeZoneError as e:
                    msg = "未知时区\"{}\"".format(para_segs[1])
            elif para_segs[0] == "price":
                assert para_segs[1].isdigit(), "价格必须为大于0的整数"
                price = int(para_segs[1])
                assert 0 < price < 1000, "价格必须为大于0小于1000的整数"
                week_start_time = get_week_start(qquser)
                existing_prices = TurnipPrice.objects.filter(user=qquser, time__gt=week_start_time)
                new_price = TurnipPrice(user=qquser, time=time.time(), price=price)
                overwrite = False
                for old_price in existing_prices:
                    if old_price.day() == new_price.day() and old_price.am_pm() == new_price.am_pm():
                        new_price = old_price
                        overwrite = True
                        break
                if overwrite:
                    new_price.time = time.time()
                    new_price.price = price
                msg = "周{}{}的大头菜{}价格已被{}为{}".format(
                    weekday_str[new_price.day()],
                    am_pm_str[new_price.am_pm()],
                    "买入" if new_price.day() == 0 else "",
                    "更新" if overwrite else "设定",
                    price
                )
                new_price.save()
            elif para_segs[0] == "info":
                msg = "时区：{}\n".format(qquser.timezone)
                _, price_msg = get_price_info(qquser)
                msg += "本周记录的大头菜价格为：\n" + price_msg
            elif para_segs[0] == "algorithm":
                msg = "[CQ:image,file=https://i.loli.net/2020/04/05/EW9ZdUxRTHMPojQ.png]"
            elif para_segs[0] == "about":
                msg = '''白萝卜价格趋势模型(简体中文)
Github: InsulatingShell
https://github.com/InsulatingShell/ACTurnipPriceModel-cn/
微博：@绝缘壳
版本：v 1.1.1
最后更新时间： Mar 25
'''
            elif para_segs[0] == "predict":
                try:
                    price_list, _ = get_price_info(qquser)
                    tunip = Turnip()
                    def s2i(x):
                        try:
                            return int(x)
                        except ValueError:
                            return -1
                    if len(para_segs) > 1:
                        price_msg = para_segs[1:]
                        price_list = []
                        for i, price in enumerate(price_msg):
                            if i == 0:
                                price_list.append(s2i(price))
                            else:
                                prices = price.split('/')
                                for price_ in prices:
                                    price_list.append(s2i(price_))
                    while price_list[-1] == -1:
                        price_list.pop()
                    msg = tunip.load_price_list(price_list)
                except AssertionError as e:
                    msg = "{}\n数据记录错误：{}".format(price_list, e)
            else:
                msg = "无效的二级命令，请使用\"/turnip help\"查看命令列表"
        msg = "[CQ:at,qq={}] {}".format(qquser, msg)
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except AssertionError as e:
        msg = "数据校验错误：{}".format(e)
        action_list.append(reply_message_action(receive, msg))
    except Exception as e:
        msg = "Error: {}".format(type(e))
        traceback.print_exc()
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return action_list
