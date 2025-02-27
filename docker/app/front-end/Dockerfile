FROM nginx:alpine

RUN apk add --no-cache openssl

COPY front-end/ /usr/share/nginx/static
COPY front-end/nginx.conf /etc/nginx/nginx.conf
COPY docker/app/front-end/generate_ssl.sh /etc/ssl/generate_ssl.sh
RUN chmod +x /etc/ssl/generate_ssl.sh && /etc/ssl/generate_ssl.sh

CMD ["nginx", "-g", "daemon off;"]
