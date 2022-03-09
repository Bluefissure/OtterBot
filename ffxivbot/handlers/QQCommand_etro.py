from .QQEventHandler import QQEventHandler
from .QQUtils import *
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.common.exceptions import NoSuchElementException
from ffxivbot.models import *
import logging
import json
import random
import requests


def QQCommand_etro(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        r = random.randint(1,6)
        gearset_id = receive["message"].replace("/etro","",1).strip()

        firefox_options = Options()
        firefox_options.add_argument("--headless")
        driver = webdriver.Firefox(executable_path='/root/OtterBot/lib/geckodriver', options=firefox_options)
        driver.get('https://etro.gg/embed/gearset/{}'.format(gearset_id))
        driver.set_window_size(800, 1200)
        try:
            ele = driver.find_element_by_xpath("//div[contains(@class,'mantine-Grid-root')]")
        except NoSuchElementException:
            msg = "找不到界面元素，请确认装备套装ID"
        else:
            msg = "[CQ:image,file=base64://{}]\nhttps://etro.gg/gearset/{}".format(ele.screenshot_as_base64, gearset_id)
        driver.quit()
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        msg = "Error: {}".format(type(e))
        action_list.append(reply_message_action(receive, msg))
        logging.error(e)
    return []
