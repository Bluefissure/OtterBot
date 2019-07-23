from ffxivbot.handlers.QQUtils import reply_message_action
from ffxivbot.models import HunterGroupID


def QQCommand_hadmin(*args, **kwargs):
    receive = kwargs["receive"]
    user_id = receive["user_id"]
    msg = ""
    action_list = []

    receive_msg = receive["message"].replace("/hadmin", "", 1).strip()
    param_segs = receive_msg.split(" ")

    while "" in param_segs:
        param_segs.remove("")
    try:
        optype = param_segs[0].strip()
    except IndexError:
        msg = ""
    if user_id == 2875726738 or user_id == 306401806:
        if optype == "add":
            try:
                set_group_id = param_segs[1].strip()
                set_group_server = param_segs[2].strip()
                set_group_remark = param_segs[3].strip()
                new_group = HunterGroupID()
                new_group.groupid = set_group_id
                new_group.servermark = set_group_server
                new_group.remark = set_group_remark
                new_group.save()
                msg = "添加成功"
            except HunterGroupID.DoesNotExist:
                msg = "添加失败"
            except IndexError:
                msg = "参数错误"
        elif optype == "del":
            try:
                set_group_id = param_segs[1].strip()
                del_group = HunterGroupID.objects.get(groupid=set_group_id)
                del_group.delete()
                msg = "删除成功"
            except HunterGroupID.DoesNotExist:
                msg = "删除失败"
            except IndexError:
                msg = "参数错误"
        elif optype == "list":
            try:
                msg = "狩猎群组：\n"
                msg_list = []
                hunt_group_list = HunterGroupID.objects.all()
                for hunt_group in hunt_group_list:
                    msg_list.append(hunt_group.groupid + "：\n" + hunt_group.remark)
                for msg_tag in msg_list:
                    msg += "{}\n".format(msg_tag)
            except HunterGroupID.DoesNotExist:
                msg = "查询失败"
    else:
        msg = "测试"
    reply_action = reply_message_action(receive, msg)
    action_list.append(reply_action)
    return action_list