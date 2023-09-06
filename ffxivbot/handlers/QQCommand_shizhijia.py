from .QQEventHandler import QQEventHandler
import time
import logging
import json
import random
import requests
import traceback

from .QQUtils import *
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.common.exceptions import NoSuchElementException, TimeoutException
from ffxivbot.models import *


def get_shizhijia_profile(uid, api_cookie, self_uid):
    firefox_options = Options()
    firefox_options.add_argument("--headless")
    firefox_options.set_preference("general.useragent.override", "Mozilla/5.0 (iPhone; CPU iPhone OS 13_2_3 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/13.0.3 Mobile/15E148 Safari/604.1")
    driver = webdriver.Firefox(options=firefox_options)
    driver.get('https://apiff14risingstones.web.sdo.com')  # 403, dummy url
    driver.delete_all_cookies()
    for cookie in api_cookie.split(';'):
        if (not cookie) or ('=' not in cookie):
            continue
        kv_list = cookie.strip().split('=')
        key, value = kv_list[0], kv_list[1]
        driver.add_cookie({'name': key, 'value': value, 'domain': 'apiff14risingstones.web.sdo.com'})
    profile_url = 'https://ff14risingstones.web.sdo.com/mob/index.html#/mhome'
    if self_uid != uid:
        profile_url += f'?uuid={uid}'
    driver.get(profile_url)
    driver.set_window_size(390, 1200)
    try:
        WebDriverWait(driver, 5).until(EC.presence_of_element_located((By.XPATH, "//div[contains(@class, 'mescroll')]/div/div")))
        time.sleep(1)
    except TimeoutException:
        if "登录" in driver.title:
            driver.quit()
            return "登录态失效，请检查COOKIE设置"
        driver.quit()
        return "无法定位关键页面元素"
    try:
        ele = driver.find_element(By.XPATH, "//div[contains(@class, 'mescroll')]/div/div")
        driver.set_window_size(390, max(ele.size['height'] + 300, 1200))
        images = driver.find_elements(By.XPATH, "//img")
        WebDriverWait(driver, 5).until(lambda driver: all(list(map(
            lambda img: driver.execute_script("return arguments[0].complete && "+
                "typeof arguments[0].naturalWidth != \"undefined\" && "+
                "arguments[0].naturalWidth > 0", img), images))))
        # ele.screenshot(f"{uid}.png")
    except NoSuchElementException:
        msg = "找不到界面元素"
    else:
        msg = "[CQ:image,file=base64://{}]".format(ele.screenshot_as_base64)
    driver.quit()
    return msg

def QQCommand_shizhijia(*args, **kwargs):
    try:
        action_list = []
        receive = kwargs["receive"]
        r = random.randint(1,6)
        user_id = receive["message"].replace("/shizhijia","",1).strip()
        (qquser, created) = QQUser.objects.get_or_create(user_id=receive["user_id"])
        try:
            msg = get_shizhijia_profile(user_id, qquser.szj_user.cookie, qquser.szj_user.user_id)
        except QQUser.szj_user.RelatedObjectDoesNotExist:
            msg = "未设置石之家绑定用户"
        reply_action = reply_message_action(receive, msg)
        action_list.append(reply_action)
        return action_list
    except Exception as e:
        logging.error(e)
        traceback.print_exc()
    return []
