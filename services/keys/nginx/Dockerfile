FROM nginx:1.25.1-alpine-slim

RUN rm /etc/nginx/conf.d/*
ADD keys.conf /etc/nginx/conf.d

RUN mkdir -p /var/www
ADD static /var/www/static
