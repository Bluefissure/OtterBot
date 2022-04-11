import re

from django.contrib import auth
from django.http import HttpResponseRedirect

from FFXIV import settings
from ffxivbot.models import *
from .ren2res import ren2res
import random
import string


def register(req):
    verification = settings.OTTER_VERIFICATION
    if req.method == "GET":
        req_dict = {"verification": verification}
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
            return ren2res("register.html", req, {"err": "Email格式错误", "verification": verification})
        elif p.match(email) == None:
            return ren2res("register.html", req, {"err": "目前仅支持QQ号邮箱注册", "verification": verification})
        elif emailresult.exists():
            return ren2res("register.html", req, {"err": "此邮箱已被注册", "verification": verification})
        elif not req.POST.get("TOS"):
            return ren2res("register.html", req, {"err": "请阅读并同意用户协议", "verification": verification})
        pw1 = req.POST.get("Password")
        if not pw1:
            return ren2res("register.html", req, {"err": "密码不能为空", "verification": verification})
        pw2 = req.POST.get("Retype password")
        if pw1 != pw2:
            return ren2res("register.html", req, {"err": "密码不匹配", "verification": verification})
        newuser = User()
        newuser.username = email
        qq = email.replace("@qq.com", "")
        (newinfo, created) = QQUser.objects.get_or_create(user_id=qq)
        if settings.OTTER_VERIFICATION:
            print(f"qq:{qq} newinfo.vcode:{newinfo.vcode} vcode:{vcode}")
            if (not newinfo.vcode) or newinfo.vcode != vcode:
                new_vcode = "".join(
                    random.choices(string.ascii_uppercase + string.digits, k=16)
                )
                newinfo.vcode = new_vcode
                newinfo.vcode_time = 0
                newinfo.save(update_fields=["vcode", "vcode_time"])
                return ren2res("register.html", req, {
                    "err": f"獭獭认证码为空或不匹配，新的獭獭认证码为\"{new_vcode}\"请于五分钟内在包含獭獭的群内输入以下命令后重试：/bot register {new_vcode}",
                    "verification": verification,
                    "vcode": new_vcode
                })
            if newinfo.vcode_time + 300 < time.time():
                return ren2res("register.html", req, {"err": "獭獭认证码已过期", "verification": verification})
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
            return ren2res("register.html", req, {"success": "注册成功", "verification": verification})
