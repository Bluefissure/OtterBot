import re

from django.contrib import auth
from django.http import HttpResponseRedirect

from FFXIV import settings
from ffxivbot.models import *
from .ren2res import ren2res


def register(req):
    if req.method == "GET":
        req_dict = {"verification": settings.OTTER_VERIFICATION}
        if req.GET.get("err"):
            req_dict.update({"err": req.GET.get("err")})
        if req.user.is_anonymous:
            if req.GET.get("next"):
                req.session["next"] = req.GET.get("next")
            return ren2res("register.html", req, req_dict)
        else:
            return HttpResponseRedirect("/")
    elif req.method == "POST":
        email = req.POST.get("Email")
        vcode = req.POST.get("Verification Code")
        emailresult = User.objects.filter(username=email)
        p = re.compile("^\d+@qq\.com$")
        if not email:
            return ren2res("register.html", req, {"err": "Email格式错误"})
        elif p.match(email) == None:
            return ren2res("register.html", req, {"err": "目前仅支持QQ邮箱注册"})
        elif emailresult.exists():
            return ren2res("register.html", req, {"err": "此邮箱已被注册"})
        elif not req.POST.get("TOS"):
            return ren2res("register.html", req, {"err": "请阅读并同意用户协议"})
        else:
            pw1 = req.POST.get("Password")
            if not pw1:
                return ren2res("register.html", req, {"err": "密码不能为空"})
            pw2 = req.POST.get("Retype password")
            if pw1 != pw2:
                return ren2res("register.html", req, {"err": "密码不匹配"})
            else:
                newuser = User()
                newuser.username = email
                qq = email.replace("@qq.com", "")
                (newinfo, created) = QQUser.objects.get_or_create(user_id=qq)
                if settings.OTTER_VERIFICATION:
                    if newinfo.vcode != vcode:
                        return ren2res("register.html", req, {"err": "獭獭认证码不匹配"})
                    if newinfo.vcode_time + 300 < time.time():
                        return ren2res("register.html", req, {"err": "獭獭认证码已过期"})
                newuser.set_password(pw1)
                newuser.save()
                newinfo.dbuser = newuser
                newinfo.vcode_time = 0
                newinfo.vcode = ""
                newinfo.save()
                newuser = auth.authenticate(username=email, password=pw1)
                auth.login(req, user=newuser)
                next = req.session.get("next")
                if next:
                    return HttpResponseRedirect(next)
                else:
                    return ren2res("register.html", req, {"success": "注册成功"})
