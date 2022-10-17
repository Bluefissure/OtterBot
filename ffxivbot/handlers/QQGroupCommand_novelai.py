from .QQEventHandler import QQEventHandler
from .QQUtils import *
from ffxivbot.models import *
import logging
import json
import random
import requests
import traceback
import re
import copy
import base64
from difflib import SequenceMatcher

NSFW_TAGS = [
    "tentacle", "hairjob", "oral", "fellatio", "deepthroat", "gokkun", "gag", "ballgag", "bitgag", "ring_gag", "cleave_gag", "panty_gag", "tapegag", "facial", "leash",
    "handjob", "groping", "areolae", "nipples", "puffy_nipples", "small_nipples", "nipple_pull", "nipple_torture", "nipple_tweak", "nipple_piercing", "breast_grab",
    "lactation", "breast_sucking", "nipple_suck", "breast_feeding", "paizuri", "multiple_paizuri", "breast_smother", "piercing", "navel_piercing", "thigh_sex", "footjob",
    "mound_of_venus", "wide_hips", "masturbation", "clothed_masturbation", "penis", "testicles", "ejaculation", "cum", "cum_inside", "cum_on_breast", "cum_on_hair",
    "cum_on_food", "tamakeri", "pussy", "vaginal", "pubic_hair", "shaved_pussy", "no_pussy", "clitoris", "fat_mons", "cameltoe", "pussy_juice", "female_ejaculation",
    "grinding", "crotch_rub", "facesitting", "cervix", "cunnilingus", "insertion", "anal_insertion", "fruit_insertion", "large_insertion", "penetration", "fisting",
    "fingering", "multiple_insertions", "double_penetration", "triple_penetration", "double_vaginal", "peeing", "have_to_pee", "ass", "huge_ass", "spread_ass", "buttjob",
    "spanked", "anus", "anal", "double_anal", "anal_fingering", "anal_fisting", "anilingus", "enema", "stomach_bulge", "wakamezake", "public", "humiliation", "bra_lift",
    "panties_around_one_leg", "caught", "walk", "body_writing", "tally", "futanari", "incest", "twincest", "pegging", "femdom", "ganguro", "bestiality", "gangbang",
    "hreesome", "group_sex", "orgy", "teamwork", "tribadism", "molestation", "voyeurism", "exhibitionism", "rape", "about_to_be_raped", "sex", "clothed_sex", "happy_sex",
    "underwater_sex", "spitroast", "cock_in_thighhigh", "69", "doggystyle", "leg_lock", "upright_straddle", "missionary", "girl_on_top", "cowgirl_position", 
    "reverse_cowgirl", "virgin", "slave", "shibari", "bondage", "bdsm", "pillory", "stocks", "rope", "bound_arms", "bound_wrists", "crotch_rope", "hogtie", "frogtie", 
    "suspension", "spreader_bar", "wooden_horse", "anal_beads", "dildo", "cock_ring", "egg_vibrator", "artificial_vagina", "hitachi_magic_wand", "dildo", "double_dildo", 
    "vibrator", "vibrator_in_thighhighs", "nyotaimori", "vore", "amputee", "transformation", "mind_control", "censored", "uncensored", "asian", "faceless_male", "blood", 
    "all_fours", "undressing", "skirt_lift", "shirt_lift", "nsfw", "porn", "lewd"
]
PROMPT_TAGS = ['masterpiece', 'best quality']
UC_TAGS = ["nsfw", "lowres", "bad anatomy", "bad hands", "text", "error", "missing fingers", "extra digit", "fewer digits", "cropped", "worst quality", "low quality", 
"normal quality", "jpeg artifacts", "signature", "watermark", "username", "blurry", "bad feet"]

def filter_nsfw(tags):
    filtered_tags = []
    for tag in tags:
        is_nsfw = False
        for nsfw_tag in NSFW_TAGS:
            score1 = SequenceMatcher(None, tag.lower(), nsfw_tag.lower()).ratio()
            score2 = SequenceMatcher(None, tag.lower(), nsfw_tag.replace('_', ' ').lower()).ratio()
            if score1 >= 0.9 or score2 >= 0.9:
                is_nsfw = True
                break
        if not is_nsfw:
            filtered_tags.append(tag)
    return filtered_tags


def generate(bot, group, msg_list):
    if not bot.novelai_url:
        return f"{bot} 未配置 novelai_url"
    url = bot.novelai_url
    if url.endswith('generate-stream'):
        url = url[:-len('generate-stream')]
    r = requests.get(url, timeout=20)
    if r.status_code != 200:
        return f"{bot} 的 novelai_url 无法访问"
    if not bot.novelai_url:
        return f"{bot} 未配置 novelai_url"
    if not bot.novelai_groups.filter(group_id=group.group_id).exists():
        return f"{bot} 未在本群开启 NovelAI 功能"
    img_url = get_CQ_image(msg_list[-1])
    img_base64 = None if not img_url else base64.b64encode(requests.get(img_url, timeout=10).content)
    try:
        prompt_text = re.sub(r'\[CQ:.*\]', '', msg_list[1])
        prompt_tags = list(map(lambda x: x.strip(), re.split('[,，]', prompt_text)))
        prompt_tags = filter_nsfw(prompt_tags)
        for tag in PROMPT_TAGS:
            if tag not in prompt_tags:
                prompt_tags.append(tag)
    except IndexError:
        return "请念咒语 (prompt 参数)"
    try:
        if '[CQ' in msg_list[2]:
            uc_tags = UC_TAGS
        else:
            uc_tags = list(map(lambda x: x.strip(), re.split('[,，]', msg_list[2])))
        for tag in UC_TAGS:
            if tag not in uc_tags:
                uc_tags.append(tag)
    except IndexError:
        uc_tags = UC_TAGS
    try:
        seed = int(msg_list[3])
    except IndexError:
        seed = random.randint(1, 2**32 - 1)
    except ValueError:
        seed = random.randint(1, 2**32 - 1)
    payload = {
        "prompt": ", ".join(prompt_tags),
        "width": 512,
        "height": 768,
        "scale": 12,
        "sampler": "k_euler_ancestral",
        "steps": 28,
        "seed": seed,
        "n_samples": 1,
        "ucPreset": 4,
        "uc": ", ".join(uc_tags),
    }
    if img_base64:
        payload['image'] = img_base64.decode()
    log_payload = copy.deepcopy(payload)
    if log_payload.get('image', ''):
        log_payload['image'] = '...'
    print(json.dumps(log_payload, indent=2))
    api_url = os.path.join(url, 'generate-stream')
    r = requests.post(api_url, json=payload, timeout=60)
    if r.status_code != 200:
        return f"{bot} 的 novelai_url 返回了错误的状态码 {r.status_code}"
    response = r.text
    try:
        image_data = response.split('\n')[2]
        image_data = image_data.replace('data:', '')
    except IndexError:
        return f"{bot} 的 novelai_url 返回了错误的响应内容"
    return '[CQ:image,file=base64://' + image_data + ']'


def QQGroupCommand_novelai(*args, **kwargs):
    action_list = []
    try:
        receive = kwargs["receive"]
        bot = kwargs["bot"]
        group = kwargs["group"]

        receive_msg = receive["message"].replace("/novelai", "", 1).strip()
        msg_list = receive_msg.split('\n')
        second_command = msg_list[0].strip()
        if second_command == "" or second_command == "help":
            msg = """
NovelAI 图片生成:
- 生成图片：
  /novelai generate
  <prompt>
  <*uc>
  <*seed>
  <*image>
按行分割，含有*的行为可选项，<>内为参数说明， image需要发送图片。"""
        elif second_command == "generate":
            msg = generate(bot, group, msg_list)
        else:
            msg = f"{bot} 看不懂这个命令捏"
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
