import feedparser
import requests
from io import BytesIO

"""
    A simple wrapper for rsshub.
"""


class RsshubUtil(object):
    def __init__(self, rsshub_base="https://rsshub.bluefissure.com"):
        self.rsshub_base = rsshub_base

    def raw_parse(self, url, relative=True):
        full_url = self.rsshub_base + url
        r = requests.get(full_url, timeout=3)
        content = BytesIO(r.content)
        return feedparser.parse(content)

    def telegram(self, router, **kwargs):
        if router == "channel":
            username = kwargs.get("username")
            if not username:
                raise Exception("No username found for channel.")
            feed = self.raw_parse("/channel/{}".format(username))
            return feed
        raise Exception('Router "{}" not supported for telegram.'.format(router))

    def live(self, platform, **kwargs):
        if platform == "bilibili":
            room_id = kwargs.get("room_id")
            if not room_id:
                raise Exception("No room_id specified.")
            feed = self.raw_parse("/bilibili/live/room/{}".format(room_id))
            return feed
        if platform == "douyu":
            room_id = kwargs.get("room_id")
            if not room_id:
                raise Exception("No room_id specified.")
            feed = self.raw_parse("/douyu/room/{}".format(room_id))
            return feed
        raise Exception('Platform "{}" not supported for live.'.format(platform))

    def biliuservedio(self, user):
        feed = self.raw_parse("/bilibili/user/video/{}".format(user))
        return feed

    def biliuserdynamic(self, user):
        feed = self.raw_parse("/bilibili/user/dynamic/{}".format(user))
        return feed
