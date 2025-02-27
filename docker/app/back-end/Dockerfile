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

CMD ["../ServerStarter.sh"]

EXPOSE 8000
