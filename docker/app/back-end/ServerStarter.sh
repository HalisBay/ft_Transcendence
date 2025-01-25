#!/bin/bash

    # if [ ! -f /usr/local/bin/dockerize ]; then
    #     curl -sSL https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz | tar -xzv -C /usr/local/bin
    #     echo "adam kral"
    # fi

    #dockerize -wait tcp://postgre:5432 -timeout 60s şerh düşüyorum
    echo "Migrate ve collect static işlemi "
    python manage.py makemigrations transcendence friends pong
    python manage.py migrate
    python manage.py collectstatic --noinput
    exec python manage.py runserver 0.0.0.0:8000
