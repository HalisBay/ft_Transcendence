FROM nginx:alpine

COPY front-end/ /usr/share/nginx/static
COPY front-end/nginx.conf /etc/nginx/nginx.conf

CMD ["nginx", "-g", "daemon off;"]
