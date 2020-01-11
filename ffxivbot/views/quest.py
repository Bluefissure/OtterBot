from django.http import JsonResponse

from ffxivbot.models import *
from .ren2res import ren2res


def quest(req):
    if req.is_ajax() and req.method == "POST":
        res_dict = {"response": "No response."}
        optype = req.POST.get("optype")
        if optype == "search_quest":
            max_iter = req.POST.get("max_iter")
            main_quest = req.POST.get("main_quest")
            main_quest = main_quest and "true" in main_quest
            sub_quest = req.POST.get("sub_quest")
            sub_quest = sub_quest and "true" in sub_quest
            start_quest = req.POST.get("start_quest").replace("任务:", "", 1)
            start_quest = PlotQuest.objects.filter(name=start_quest)
            start_quest = start_quest[0] if start_quest else None
            end_quest = req.POST.get("end_quest")
            end_quest = PlotQuest.objects.filter(name=end_quest)
            end_quest = end_quest[0] if end_quest else None
            max_iter = req.POST.get("max_iter")
            print("main_quest:{}".format(main_quest))
            print("sub_quest:{}".format(sub_quest))
            print("start_quest:{}".format(start_quest))
            quest_dict = {}
            tmp_edge_list = []
            edge_list = []
            if not start_quest and not end_quest:
                res_dict["response"] = "找不到对应任务"
            elif start_quest and end_quest:
                res_dict["response"] = "TODO: Double Quest Search"
            else:
                single_quest = start_quest or end_quest
                search_list = []
                search_iter = 0
                search_list.append((single_quest, 1, 1))
                search_list.append((single_quest, 2, 1))
                if (single_quest.is_main_scenario() and not main_quest) or (
                        not single_quest.is_main_scenario() and not sub_quest
                ):
                    res_dict["response"] = "查询任务类别与所选类别不符，清选择正确的类别。"
                    return JsonResponse(res_dict)
                done_cnt = 0
                tot_cnt = 0
                while search_list and search_iter <= min(int(max_iter), 1000):
                    try:
                        (now_quest, direction, search_iter) = search_list[0]
                        search_list = search_list[1:]
                        if single_quest.is_main_scenario():
                            if not main_quest:
                                continue
                        elif not sub_quest:
                            continue
                        if direction == 2:
                            done_cnt += 1
                        now_quest_dict = {
                            "description": "",
                            "startnpc": "",
                            "endnpc": "",
                        }
                        if now_quest.name not in quest_dict.keys():
                            quest_dict[now_quest.name] = now_quest_dict
                        else:
                            if now_quest.name != single_quest.name:
                                continue
                        if not now_quest.endpoint:
                            if direction == 1:
                                for quest in now_quest.suf_quests.all():
                                    if (quest.is_main_scenario() and main_quest) or \
                                            (not quest.is_main_scenario() and sub_quest):
                                        if quest.name not in quest_dict.keys():
                                            search_list.append((quest, 1, search_iter + 1))
                                        edge = {"from": now_quest.name, "to": quest.name}
                                        if edge not in edge_list:
                                            tmp_edge_list.append(edge)
                        if not now_quest.endpoint or (
                                now_quest.endpoint and now_quest.name == single_quest.name
                        ):
                            if direction == 2:
                                for quest in now_quest.pre_quests.all():
                                    if (quest.is_main_scenario() and main_quest) or \
                                            (not quest.is_main_scenario() and sub_quest):
                                        if quest.name not in quest_dict.keys():
                                            search_list.append((quest, 2, search_iter + 1))
                                        edge = {"from": quest.name, "to": now_quest.name}
                                        if edge not in edge_list:
                                            tmp_edge_list.append(edge)
                    except Exception as e:
                        print(e)
                for edge in tmp_edge_list:
                    if (
                            edge["from"] in quest_dict.keys()
                            and edge["to"] in quest_dict.keys()
                    ):
                        edge_list.append(edge)
                quest_dict[single_quest.name]["style"] = "fill: #7f7"
                tot_cnt = len(quest_dict.keys())
                perc = done_cnt / tot_cnt * 100
                perc = min(100, perc)
                perc = max(0, perc)
                res_dict["percentage"] = perc
                res_dict["quest_dict"] = quest_dict
                res_dict["quest_dict"] = quest_dict
                res_dict["edge_list"] = edge_list
                res_dict["response"] = "success"
        return JsonResponse(res_dict)
    return ren2res("quest.html", req, {})