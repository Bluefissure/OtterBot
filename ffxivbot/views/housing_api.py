
import re
import json
import hashlib
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from ffxivbot.models import HousingPreset


@csrf_exempt
def housing_api(req):
    # All http status here are 200 because other status will raise a C# webclient error
    base_api_regex = r"^\/housing\/api\/"
    if req.method == "POST":
        if re.match(base_api_regex + r"index\.php", req.path):
            LocationId = req.POST.get("LocationId")
            UploadName = req.POST.get("UploadName")
            Items = req.POST.get("Items")
            Tags = req.POST.get("Tags")
            Uploader = req.POST.get("Uploader")
            UserId = req.POST.get("UserId")
            if Items == "" or UploadName == "":
                return HttpResponse("Fail: Item and name cannot be empty.", status=200)
            md5 = hashlib.md5()
            md5.update(Items.encode("utf-8"))
            items_hash = md5.hexdigest()
            if HousingPreset.objects.filter(items_hash=items_hash).count() > 0:
                return HttpResponse("Fail: Preset already exists.", status=200)
            (hp, created) = HousingPreset.objects.get_or_create(
                location_id=int(LocationId),
                name=UploadName,
                items=Items,
                tags=Tags,
                uploader=Uploader,
                items_hash=items_hash,
                user_id=UserId,
            )
            if created:
                hp.save()
            return HttpResponse(
                "Success: uploaded as {}".format(items_hash), status=200
            )
        return HttpResponse(req.path, status=200)
    elif req.method == "GET":
        if re.match(base_api_regex + r"map.json", req.path):
            presets = map(
                lambda x: {
                    "LocationId": x.location_id,
                    "Name": x.name,
                    "Hash": x.items_hash,
                    "Tags": x.tags,
                    "ObjectId": "",
                },
                HousingPreset.objects.all(),
            )
            jstr = json.dumps(list(presets))
            return HttpResponse(jstr, status=200)
        mgroup = re.match(base_api_regex + r"result\/(.*).json", req.path)
        if mgroup:
            items_hash = mgroup.group(1)
            presets = HousingPreset.objects.filter(items_hash=items_hash)
            if presets.count() != 1:
                return HttpResponse("Fail: Unable to find such preset.", status=200)
            preset = presets[0]
            return HttpResponse(preset.items, status=200)
    return HttpResponse("Default API Error, contact dev please.", status=500)
