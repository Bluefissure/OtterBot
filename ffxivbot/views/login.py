from django.contrib import auth
from django.http import HttpResponseRedirect

from .ren2res import ren2res


def login(req):
    if req.method == 'GET':
        if req.user.is_anonymous:
            if req.GET.get('next'):
                req.session['next'] = req.GET.get('next')
            return ren2res("login.html", req, {})
        else:
            return HttpResponseRedirect("/tata")
    elif req.method == 'POST':
        user = auth.authenticate(username=req.POST.get('Email'), password=req.POST.get('Password'))
        if user:
            auth.login(req, user)
            next = req.session.get('next', '/tata')
            return HttpResponseRedirect(next)
        else:
            return ren2res("login.html", req, {'err': "用户名或密码错误！"})
