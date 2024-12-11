FROM nginx:alpine

COPY front-end/assets /usr/share/nginx/static
COPY front-end/nginx.conf /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]
