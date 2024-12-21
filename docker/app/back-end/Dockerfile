FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    make

COPY requirements.txt /app/
RUN pip3 install -r requirements.txt


ENV PYTHONUNBUFFERED 1

RUN touch halis.txt
#entrypoint eklencek : python manage.py migrate && python manage.py makemigrations transcendence && python manage.py sqlmigrate 001 
#makemigrations
CMD ["bash", "-c", "python manage.py migrate && python manage.py makemigrations transcendence && python manage.py migrate && python manage.py collectstatic --noinput && python manage.py runserver 0.0.0.0:8000"]


EXPOSE 8000
