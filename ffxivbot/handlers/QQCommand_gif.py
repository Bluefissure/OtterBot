from .QQEventHandler import QQEventHandler
from ffxivbot.models import *
import logging
import json
import random
import requests
#deprecated since website down
class QQCommand_gif(QQEventHandler):
    def __init__(self, **kwargs):
        super(QQCommand_gif, self).__init__()
    def __call__(self, **kwargs):
        try:
            global_config = kwargs["global_config"]
            QQ_BASE_URL = global_config["QQ_BASE_URL"]
            SORRY_BASE_URL = global_config["SORRY_BASE_URL"]
            action_list = []
            receive = kwargs["receive"]
            return [self.reply_message_action(receive, "由于网站关闭，/gif功能已弃用")]
            
            # sorry_dict = {"sorry":"好啊|就算你是一流工程师|就算你出报告再完美|我叫你改报告你就要改|毕竟我是客户|客户了不起啊|sorry 客户真的了不起|以后叫他天天改报告|天天改 天天改","wangjingze":"我就是饿死|死外边 从这跳下去|也不会吃你们一点东西|真香","jinkela":"金坷垃好处都有啥|谁说对了就给他|肥料掺了金坷垃|不流失 不蒸发 零浪费|肥料掺了金坷垃|能吸收两米下的氮磷钾","marmot":"啊~|啊~~~","dagong":"没有钱啊 肯定要做的啊|不做的话没有钱用|那你不会去打工啊|有手有脚的|打工是不可能打工的|这辈子不可能打工的","diandongche":"戴帽子的首先进里边去|开始拿剪刀出来 拿那个手机|手机上有电筒 用手机照射|寻找那个比较新的电动车|六月六号 两名男子再次出现|民警立即将两人抓获"}
            # sorry_name = {"sorry":"为所欲为","wangjingze":"王境泽","jinkela":"金坷垃","marmot":"土拨鼠","dagong":"窃格瓦拉","diandongche":"偷电动车"}
            # receive_msg = receive["message"].replace('/gif','',1).strip()
            # if receive_msg=="list":
            #     msg = ""
            #     for (k,v) in sorry_dict.items():
            #         msg = msg + "%s : %s\n"%(k,sorry_name[k])
            # else:
            #     now_template = ""
            #     for (k,v) in sorry_dict.items():
            #         if (receive_msg.find(k)==0):
            #             now_template = k
            #             break
            #     if (now_template=="" or len(receive_msg)==0 or receive_msg=="help"):
            #         msg = "/gif list : 目前可用模板\n/gif $template example : 查看模板$template的样例\n/gif $template $msg0|$msg1|... : 按照$msg0,$msg1...生成沙雕GIF\nPowered by sorry.xuty.tk"
            #     else:
            #         receive_msg = receive_msg.replace(now_template,"",1).strip()
            #         if(receive_msg=="example"):
            #             msg = sorry_dict[now_template]
            #         else:
            #             msgs = receive_msg.split('|')
            #             cnt = 0
            #             gen_data = {}
            #             for sentence in msgs:
            #                 sentence = sentence.strip()
            #                 if(sentence==""):
            #                     continue
            #                 gen_data[str(cnt)] = sentence
            #                 logging.debug("sentence#%s:%s"%(cnt,sentence))
            #                 cnt += 1
            #             if(cnt==0):
            #                 msg = "至少包含一条字幕消息"
            #             else:
            #                 logging.debug("gen_data:%s"%(json.dumps(gen_data)))
            #                 url = SORRY_BASE_URL + "/api/%s/make"%(now_template)
            #                 try:
            #                     s = requests.post(url=url,data=json.dumps(gen_data),timeout=2)
            #                     img_url = SORRY_BASE_URL + s.text
            #                     logging.debug("img_url:%s"%(img_url))
            #                     msg = '[CQ:image,cache=0,file='+img_url+']'
            #                 except Exception as e:
            #                     msg = "SORRY API ERROR:%s"%(type(e))
            #                     logging.debug(msg)
            #                     self.send_message(receive["message_type"], group_id or user_id, msg)
            # msg = msg.strip()
            # reply_action = self.reply_message_action(receive, msg)
            # action_list.append(reply_action)
            # return action_list
        except Exception as e:
            msg = "Error: {}".format(type(e))
            action_list.append(self.reply_message_action(receive, msg))
            logging.error(e)