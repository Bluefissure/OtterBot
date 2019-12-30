from ffxivbot.models import *
import requests, base64
terr = Territory.objects.get(name="黑风海")
for i in range(1, 9):
    url = "http://tools.ffxiv.cn/lajipai/image/dig/%E7%BC%A0%E5%B0%BE%E8%9B%9F%E9%9D%A9/baofeng{}.jpeg".format(i)
    res = requests.get(url=url, timeout=5)
    uri = "data:" + res.headers['Content-Type'] + ";" +"base64," + base64.b64encode(res.content).decode("utf-8")
    t = TreasureMap(territory=terr)
    t.rank = "G12"
    t.uri = uri
    t.number = i
    print("Adding TreasureMap {}".format(t))
    t.save()
