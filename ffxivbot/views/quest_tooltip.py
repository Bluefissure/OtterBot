import urllib

import requests
from bs4 import BeautifulSoup
from django.http import HttpResponse

from ffxivbot.models import PlotQuest
from .ren2res import ren2res


def quest_tooltip(req):
    quest_id = req.GET.get("id", 0)
    nocache = req.GET.get("nocache", "False") == "True"
    res_type = req.GET.get("type", "web")
    print("quest_id:{}".format(quest_id))
    try:
        if quest_id:
            try:
                quest = PlotQuest.objects.get(id=quest_id)
            except PlotQuest.DoesNotExist:
                return HttpResponse("No such quest", status=500)
            else:
                if res_type == "web":
                    if quest.tooltip_html == "" or nocache:
                        r = requests.get(
                            "https://ff14.huijiwiki.com/ff14/api.php\
                            ?format=json&action=parse&disablelimitreport=true&prop=text&title=%E9%A6%96%E9%A1%B5\
                            &smaxage=86400&maxage=86400&text=%7B%7B%E4%BB%BB%E5%8A%A1%2F%E6%B5%AE%E5%8A%A8%E6%91%98%E8%A6%81%7C{}%7D%7D".format(
                                quest_id
                            ), timeout=5)
                        r_json = r.json()
                        # print(r_json)
                        html = r_json["parse"]["text"]["*"]
                        html = html.replace("class=\"tooltip-item\"", "class=\"tooltip-item\" id=\"tooltip\"", 1)
                        html = html.replace("href=\"/", "href=\"https://ff14.huijiwiki.com/")
                        soup = BeautifulSoup(html, 'html.parser')
                        quest_name = soup.p.span.string
                        a = soup.new_tag('a', href='https://ff14.huijiwiki.com/wiki/%E4%BB%BB%E5%8A%A1:{}'.format(
                            urllib.parse.quote(quest_name)))
                        a.string = quest_name
                        soup.p.span.string = ""
                        soup.p.span.append(a)
                        html = str(soup)
                        quest.tooltip_html = html
                        quest.save(update_fields=["tooltip_html"])
                    else:
                        html = quest.tooltip_html
                    return ren2res("quest_tooltip.html", req, {"parsed_html": html})
                elif res_type == "img" or res_type == "image":
                    return HttpResponse("TODO", status=500)
    except KeyError:
        return HttpResponse("KeyError", status=500)
    return HttpResponse(status=500)