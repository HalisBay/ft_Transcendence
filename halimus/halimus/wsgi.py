"""
WSGI config for halimus project.

It exposes the WSGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/5.1/howto/deployment/wsgi/
"""

import os
import debugpy

from django.core.wsgi import get_wsgi_application
from django.shortcuts import render


if os.getenv("DJANGO_DEBUG", "False") == "True":
    print("Starting debugpy...")
    debugpy.listen(("0.0.0.0", 5678))  # Bind debugpy to the specified port
    print("Debugger is active, waiting for VS Code to attach...")

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'halimus.settings')

application = get_wsgi_application()