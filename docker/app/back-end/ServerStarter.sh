#!/bin/bash

if [ ! -f /app/migrations_done ]; then
    python manage.py migrate
    python manage.py makemigrations transcendence
    python manage.py migrate
    touch /app/migrations_done
fi
    python manage.py migrate
    python manage.py runserver 0.0.0.0:8000
