# Temel Python 3.11 slim imajını kullanıyoruz
FROM python:3.11-slim

# Çalışma dizinini belirleyin

# Django ve diğer bağımlılıkları manuel olarak yükleyin
WORKDIR /app


RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    gcc \
    make

COPY requirements.txt /app/
RUN pip3 install -r requirements.txt

# Django ortam değişkenini ayarlayın
ENV PYTHONUNBUFFERED 1

# Uygulamayı başlatmak için komut
CMD ["bash", "-c", "python manage.py migrate && python manage.py runserver 0.0.0.0:8000"]


# Portu açın
EXPOSE 8000
