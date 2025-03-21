#!/bin/bash

echo "Migrate and collect static process "
python manage.py makemigrations transcendence friends pong
python manage.py migrate
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8000
