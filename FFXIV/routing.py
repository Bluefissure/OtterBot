from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter, ChannelNameRouter
import ffxivbot.consumers as consumers
from django.urls import re_path

application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter([
            # url(r'^ws_api', consumers.APIConsumer),
            # url(r'^ws_event', consumers.EventConsumer),
            re_path(r'^ws(?!_)', consumers.WSConsumer.as_asgi()),
        ])
    )
})
