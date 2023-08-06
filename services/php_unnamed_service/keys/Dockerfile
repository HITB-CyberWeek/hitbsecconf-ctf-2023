FROM php:8.2-fpm-alpine

RUN apk add --update autoconf alpine-sdk
RUN pecl install redis

RUN mkdir -p /var/www
ADD index.php /var/www

EXPOSE 9000
