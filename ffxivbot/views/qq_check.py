import time

from django.contrib import auth
from django.http import HttpResponseRedirect

from FFXIV import settings
from ffxivbot.models import QQUser
from ffxivbot.oauth_client import OAuthQQ


def qq_check(req):
    code = req.GET.get('code', None)
    authqq = OAuthQQ(settings.QQ_APP_ID, settings.QQ_KEY, settings.QQ_RECALL_URL)
    access_token = authqq.get_access_token(code)
    time.sleep(0.05)
    qq_openid = authqq.get_open_id()
    try:
        qquser = QQUser.objects.get(open_id=qq_openid)
        user = qquser.dbuser
        auth.login(req, user)
        next = req.session.get('next', '/tata')
        return HttpResponseRedirect(next)
    except QQUser.DoesNotExist:
        if req.user.is_anonymous:
            return HttpResponseRedirect(
                "/register/?err=%E8%AF%B7%E9%A6%96%E5%85%88%E6%B3%A8%E5%86%8C%E8%B4%A6%E6%88%B7%E5%B9%B6%E7%BB%91%E5%AE%9AQQ")
        else:
            user = req.user
            qquser = user.qquser
            qqinfo = authqq.get_qq_info()
            qquser.open_id = qq_openid
            if qqinfo.get("ret", -1) == 0:
                qquser.nickname = qqinfo.get("nickname")
                qquser.avatar_url = qqinfo.get("figureurl_qq")
                if qquser.avatar_url.startswith("http://"):
                    qquser.avatar_url = qquser.avatar_url.replace("http://", "https://")
            qquser.save()
            next = req.session.get('next', '/tata')
            return HttpResponseRedirect(next)
    return HttpResponseRedirect("/tata")
