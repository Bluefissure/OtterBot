import requests
from .constants import MAP_ID2NAME, MAP_NAME2ID_FFXIVEUREKA, MAP_NAME2ID_FFXIVSC

def nm_id2name(fate_id):
    return "" if fate_id not in MAP_ID2NAME else MAP_ID2NAME[fate_id]

def get_nm_id(tracker, nm_name):
    if tracker == "ffxiv-eureka":
        name_id = MAP_NAME2ID_FFXIVEUREKA
        for (k, v) in name_id.items():
            if k in nm_name:
                return v
    elif tracker == "ffxivsc":
        name_id = MAP_NAME2ID_FFXIVSC
        for (k, v) in name_id.items():
            if k in nm_name:
                return v
        return {"level": -1, "type": -1}
    return -1

def fate_id2name(fate_id):
    r = requests.get(
        "http://cafemaker.wakingsands.com/Fate/{}".format(fate_id), timeout=3
    )
    j = r.json()
    return j.get("Name")