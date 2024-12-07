# Temel Python 3.11 slim imajını kullanıyoruz
FROM python:3.11-slim

# Çalışma dizinini belirleyin
WORKDIR /app

# Django ve diğer bağımlılıkları manuel olarak yükleyin
RUN pip3 install --no-cache-dir \
    "django>=4.0,<5.0" \
    "psycopg2-binary>=2.9.0" \
    "django-environ"

# Django ortam değişkenini ayarlayın
ENV PYTHONUNBUFFERED 1

# Uygulamayı başlatmak için komut
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]

# Portu açın
EXPOSE 8000
