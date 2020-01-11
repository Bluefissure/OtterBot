import re

from django.http import JsonResponse
from django.shortcuts import render


def ren2res(template: str, req, dict={}, json_res=False):
    if req.user.is_authenticated:
        qquser = req.user.qquser
        p = re.compile('^[0-9a-zA-Z_]+$')
        dict.update({'user': {
            "nickname": qquser.nickname,
            "avatar": qquser.avatar_url
        }})
    else:
        dict.update({'user': False})
    if req:
        if json_res and req.is_ajax() and req.method == 'GET':
            return JsonResponse(dict)
        return render(req, template, dict)
    else:
        return render(req, template, dict)