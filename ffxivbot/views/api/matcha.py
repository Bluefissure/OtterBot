import json
from .utils import nm_id2name, fate_id2name

def get_matcha_nm_name(req):
    nm_name = ""
    try:
        matcha_json = json.loads(req.body)
        if matcha_json.get("event") == "Fate":
            incoming_data = matcha_json.get("data")
            event_type = incoming_data.get("type")
            if event_type == "start":
                fate_id = incoming_data.get("fate")
                nm_name = nm_id2name(fate_id)
            else:
                pass
                # print("Won't handle fate event other than 'start'.")
    except json.JSONDecodeError:
        pass
    return nm_name


def get_matcha_fate_name(req):
    fate_name = ""
    try:
        matcha_json = json.loads(req.body)
        if matcha_json.get("event") == "Fate":
            incoming_data = matcha_json.get("data")
            event_type = incoming_data.get("type")
            if event_type == "start":
                fate_id = incoming_data.get("fate")
                fate_name = fate_id2name(fate_id)
            else:
                pass
                # print("Won't handle fate event other than 'start'.")
    except json.JSONDecodeError:
        pass
    return fate_name