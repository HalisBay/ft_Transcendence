#!/bin/bash

echo "Migrate ve collect static işlemi "
python manage.py makemigrations transcendence friends pong
python manage.py migrate
python manage.py collectstatic --noinput
exec python manage.py runserver 0.0.0.0:8000
