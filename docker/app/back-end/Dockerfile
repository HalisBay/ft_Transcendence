FROM python:3.11-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    make \
    curl

RUN pip install Pillow
COPY requirements.txt .
RUN pip3 install -r requirements.txt
COPY app/back-end/ServerStarter.sh ../
RUN chmod +x ../ServerStarter.sh
ENV PYTHONUNBUFFERED=1

RUN touch halis.txt
#RUN curl -sSL https://github.com/jwilder/dockerize/releases/download/v0.6.1/dockerize-linux-amd64-v0.6.1.tar.gz | tar -xzv -C /usr/local/bin || true
#entrypoint eklencek : python manage.py migrate && python manage.py makemigrations transcendence && python manage.py sqlmigrate 001 
#makemigrations
CMD ["../ServerStarter.sh"]
#ENTRYPOINT ["/bin/bash", "-c", "tail -f /dev/null"]

EXPOSE 8000
