# Temel imaj olarak Nginx kullanıyoruz
FROM nginx:alpine

# Statik dosyaları Nginx sunucusuna kopyalıyoruz
COPY front-end/assets /usr/share/nginx/html
COPY front-end/nginx.conf /etc/nginx/nginx.conf

# Nginx'i çalıştırıyoruz
CMD ["nginx", "-g", "daemon off;"]
