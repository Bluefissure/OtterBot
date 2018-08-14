from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import ffxivbot.consumers as consumers
from django.conf.urls import url
application = ProtocolTypeRouter({
    # (http->django views is added by default)
    'websocket': AuthMiddlewareStack(
        URLRouter([
	    	url(r'^ws_api', consumers.APIConsumer),
	    	url(r'^ws_event', consumers.EventConsumer),
	    	url(r'^ws', consumers.WSConsumer),
	    ])
    ),
})