"""
ASGI config for halimus project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/asgi/
"""

import os

from channels.auth import AuthMiddlewareStack
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter

import pong.routing
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'halimus.settings')

application = ProtocolTypeRouter({
    'https' : get_asgi_application(),
    'websocket': AuthMiddlewareStack(
        URLRouter(
            pong.routing.websocket_urlpatterns
        )
    )
})
