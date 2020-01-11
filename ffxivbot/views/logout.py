from django.contrib import auth
from django.http import HttpResponseRedirect


def logout(req):
    auth.logout(req)
    return HttpResponseRedirect('/')
