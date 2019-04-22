from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
from bs4 import BeautifulSoup
import urllib
import logging
import time
import traceback



def QQCommand_joke(*args, **kwargs):
    action_list = []
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        FF14WIKI_API_URL = global_config["FF14WIKI_API_URL"]
        FF14WIKI_BASE_URL = global_config["FF14WIKI_BASE_URL"]
        receive = kwargs["receive"]

        bot = kwargs["bot"]
        msg = ""
        receive_msg = receive["message"].replace("/joke", "", 1).strip()
        second_command = receive_msg.split(" ")[0].strip()
        second_msg = receive_msg.replace(second_command, "", 1).strip()
        if second_command=="help" or second_command=="":
            msg = "/joke $thing|$man|$theory|$victim|$range:讽刺笑话\n"
            msg += "  $thing:要讽刺的事情是？\n"
            msg += "  $man:这件事是谁提出来的？\n"
            msg += "  $theory:提出者声称这件事有助于什么？\n"
            msg += "  $victim:这件事针对的是哪些人？\n"
            msg += "  $range:这件事起作用的范围？"
        else:
            segs = receive_msg.strip().split("|")
            while "" in segs:
                segs.remove("")
            if len(segs)!=5:
                msg = "参数数量错误($thing|$man|$theory|$victim|$range)"
            else:
                mthing, mman, mtheory, mvictim, mrange = segs
                jokes = [
  "在mrange庆典的聚会上，一位35岁的mvictim高举着牌子，上面写着“感谢mthing赐予我的快乐的童年”。\nmman呵斥道，“你是在嘲讽mthing吗？mthing才实行了20年。”\n“确切地说，这正是我感谢它的原因。”\n",
  "mman发言道：“从下个礼拜开始我们要做两件事，一，全面在mrange实行mthing；二，周六所有mvictim都要去酒吧里拿一条蜥蜴。大家有什么意见可以提出来。”\n过了一会儿，台下有个声音怯生生地提问：“为什么要拿蜥蜴？”\n“很好，我就知道大家对mthing没有异议。”\n",
  "“mthing真**的智障！”\n“你涉嫌恶意攻击mman,跟我走一趟。”\n“我又没说是哪里的mthing！”\n“废话！哪里的mthing智障我会不知道吗！”\n",
  "mman在向mvictim们讲话：\n“很快我们就能mtheory！”\n台下传来一个声音：“那我们怎么办？”\n",
  "一个mvictim的鹦鹉丢了。这是只会说话的鹦鹉，要是落到mman的手里可糟了。\n这人便发表了一篇声明：“本人遗失鹦鹉一只，另外，本人不同意它关于mthing的观点。”\n",
  "“mthing是艺术还是科学?”\n”我说不好，但肯定不是科学。”\n“何以见得?”\n“如果mthing是科学的话，他们至少应该先用小白鼠做实验。”\n",
  "大会主持人:”请支持mthing的人坐在左边，反对mthing的坐在右边。”\n大多数人坐在了右边，少数人坐在了左边，只有一个人坐在中间纹丝不动。\n主持人很不解，询问情况。\n“我对mvictim们的情况表示十分理解，但我支持mthing。”\n”那您赶快坐到主席台来。”主持人急忙说道。\n",
  "mman关于“关爱mvictim 支持mthing”的会议纪要正在以超光速增长，但这并没有违背相对论，因为会议纪要里不含有任何信息。\n",
  "mman:“我们要不惜一切代价，为了我们的主人翁mtheory！”\n一个mvictim对另一个mvictim说:“看哪 ，mman把咱们当主人翁。”\n另一个mvictim说:“不，我们是‘代价’。”\n",
  "“如果你在mrange，旁边一个陌生人突然开始唉声叹气，正确的做法是什么?”\n“立即阻止这种反对mthing的行为。”\n",
  "mman:“由于mthing的实行，各位mvictim的美好未来前景已经出现在了地平线上。”\n一个mvictim问另一个mvictim:”什么是地平线?”\n另一个mvictim回答道:“就是那个能看到但是永远都到不了的线。”\n",
  "mman在mrange随机采访了一位mvictim:“请问你对mthing有什么意见吗?”\nmvictim答道:“我有一些意见，但我不同意我的意见!”\n",
  "两个骷髅相遇，一骷髅问另一个骷髅:“我是被mman的mthing逼死的，你是怎么死的？”\n另一个骷髅回答说:“我还活着。”\n",
  "mman的汽车被一头牛挡住了，怎么也赶不走。mman便下车对牛说：“你再不走，我就把你送到mrange去mthing。”牛听了便一溜烟的跑开了。\n",
  "问：“mthing的优越之处是什么？”\n答：“成功克服了那些其他情况下不会存在的困难。”\n",
  "问：“mthing在哪些时候会遇到抵制？”\n答：“主要有四个时间段：春天、夏天、秋天和冬天。”\n",
  "mman问一名mvictim:“你的爸爸是谁？”\n他回答说：“是mman!”\nmman很满意，又问：“你的母亲是谁？”\n他回答：“是mthing！”\nmman又问：“你将来想当什么？”\n“孤儿！”\n",
  "问：“什么是最短的笑话？”\n答：“mthing。”\n",
  "问：“那些别有用心的人是怎样黑mthing的？”\n答：“他们把mman说的内容原文复述了。”\n",
  "问：“为什么mman把mvictim放在中心考虑？”\n答：“这样从各个方向都能方便地欺压他们。”\n",
  "问：“什么叫交换意见？”\n答：“带着你的意见去找mman理论，然后带着他的回来。”\n",
  "问：“mthing实行的结果如何？”\n答：“还是有人活下来了。”\n",
  "问：“mthing的前景是什么？”\n答：“有两种可能的情况。现实的可能是火星人会降临地球帮我们打理一切，科幻的可能是我们成功地mtheory。”\n"
]
                joke = random.choice(jokes)
                joke = joke.replace("mthing", mthing)
                joke = joke.replace("mman", mman)
                joke = joke.replace("mtheory", mtheory)
                joke = joke.replace("mvictim", mvictim)
                joke = joke.replace("mrange", mrange)
                msg = joke
        if type(msg) == str:
            msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        logging.error(e)
        traceback.print_exc()
    return action_list
