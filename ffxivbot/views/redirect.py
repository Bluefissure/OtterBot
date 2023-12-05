from django.http import HttpResponse, HttpResponseRedirect

REDIRECT_MAP = {
    'otterbot': 'https://qun.qq.com/qunpro/robot/qunshare?robot_uin=2854203480',
    'otterbot-guild': 'https://qun.qq.com/qunpro/robot/share?robot_appid=102006036',
}

def redirect(__, slug):
    url = REDIRECT_MAP.get(slug, '')
    if not url:
        return HttpResponse("Not Found", status=404)
    return HttpResponseRedirect(url)
