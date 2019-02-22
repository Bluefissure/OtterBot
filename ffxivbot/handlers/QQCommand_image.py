from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
from bs4 import BeautifulSoup
def get_image_from_CQ(CQ_text):
    if "url=" in CQ_text:
        tmp = CQ_text
        tmp = tmp[tmp.find("url="):-1]
        tmp = tmp.replace("url=","")
        img_url = tmp.replace("]","")
        return img_url
    return None

def upload_image(img_url):
    original_image = requests.get(url=img_url)
    sm_req = requests.post(url="https://sm.ms/api/upload",files={"smfile":original_image.content})
    return json.loads(sm_req.text)

def delete_image(img_hash):
    sm_req = requests.post(url="https://sm.ms/api/delete/{}".format(img_hash))
    return sm_req.status_code


def QQCommand_image(*args, **kwargs):
    try:
        global_config = kwargs["global_config"]
        QQ_BASE_URL = global_config["QQ_BASE_URL"]
        action_list = []
        receive = kwargs["receive"]
        
        receive_msg = receive["message"].replace('/image','',1).strip()
        msg_list = receive_msg.split(" ")
        second_command = msg_list[0]
        if second_command=="" or second_command=="help":
            msg = " 禁止上传R18/NSFW图片：\n/image upload $category $image : 给类别$category上传图片\n/image $category : 随机返回一张$category的图片\n/image del $name : 删除名为$name的图片\nPowered by https://sm.ms"
        elif second_command=="upload":
            if(len(msg_list)<3):
                msg = "您输入的参数个数不足：\n/image upload $category $image : 给类别$category上传图片"
            else:
                (qquser, created) = QQUser.objects.get_or_create(user_id=receive["user_id"])
                if not qquser.able_to_upload_image:
                    msg = "[CQ:at,qq={}] 您由于触犯规则无权上传图片".format(receive["user_id"])
                else:
                    category = msg_list[1].strip()
                    CQ_text = msg_list[2].strip()
                    img_url = get_image_from_CQ(CQ_text)
                    if(not img_url):
                        msg = "未发现图片信息"
                    else:
                        img_info = upload_image(img_url)
                        if img_info["code"]!="success":
                            msg = img_info["msg"]
                        else:
                            img_info = img_info["data"]
                            img = Image(key=category,
                                        name=img_info["storename"],
                                        path=img_info["path"],
                                        img_hash=img_info["hash"],
                                        timestamp=img_info["timestamp"],
                                        add_by=qquser)
                            img.save()
                            msg = "图片\"{}\"上传成功".format(img.name)
        elif second_command=="del":
            if(len(msg_list)<2):
                msg = "您输入的参数个数不足：\n/image del $name : 删除名为$name的图片"
            else:
                name = msg_list[1].strip()
                (qquser, created) = QQUser.objects.get_or_create(user_id=receive["user_id"])
                imgs = Image.objects.filter(name=name, add_by=qquser)
                if not imgs.exists():
                    msg = "未找到名为\"{}\"的图片或您无权删除这张图片".format(name)
                else:
                    for img in imgs:
                        img.delete()
                    msg = "图片\"{}\"删除完毕".format(name)
        else:
            category = msg_list[0].strip()
            imgs = Image.objects.filter(key=category)
            if not imgs.exists():
                msg = "未找到类别\"{}\"的图片".format(category)
            else:
                img = random.sample(list(imgs), 1)[0]
                msg = "[CQ:image,cache=0,file={}]\n".format("https://i.loli.net"+img.path)
                msg += "{}\nCategory:{}\nUploaded by:{}\n".format(img.name, img.key, img.add_by)
        msg = msg.strip()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)