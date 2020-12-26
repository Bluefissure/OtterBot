from django.db.models import Q
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse

from ffxivbot.models import *
from .ren2res import ren2res

@login_required(login_url='/login/')
def image(req):
    if req.is_ajax() and req.method == "POST":
        res_dict = {"response": "No response."}
        json_req = json.loads(req.body)
        optype = json_req.get("optype")
        if optype == "get_images":
            cat = json_req.get("category", "")
            cached_images = json_req.get("cached_images", [])
            image_filter = Image.objects.order_by('?').exclude(name__in=cached_images)
            if cat:
                image_filter = image_filter.filter(Q(key__contains=cat) | Q(add_by__user_id__contains=cat))
            images = list(
                map(
                    lambda x: {
                        "name": x.name,
                        "url": (x.get_url()),
                        "category": x.key,
                        "info": "Name:{}\nCategory:{}\nUploader:{}".format(x.name, x.key, x.add_by)
                    },
                    list(image_filter[:30]),
                )
            )
            res_dict = {"images": images, "response": "success"}
        else:
            res_dict = {"msg": "not support", "response": "error"}
        return JsonResponse(res_dict)

    return ren2res("image.html", req, {})
