import feedparser

class RsshubUtil(object):
    def __init__(self, rsshub_base="https://rsshub.bluefissure.com")
        self.rsshub_base = rsshub_base
    
    def raw_parse(self, url, relative=True):
        full_url = this.rsshub_base + url
        return feedparser.parse(full_url)

    def telegram(self, router, **kwargs):
        if router == "channel":
            username = kwargs.get("username")
            if not username:
                raise Exception("No username found for channel.")
            feed = self.raw_parse("/channel/{}".format(username))
            return feed
        raise Exception("Router not supported for telegram.")
