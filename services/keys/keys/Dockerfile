FROM php:8.2-fpm-alpine

RUN apk add --update autoconf alpine-sdk
RUN pecl install redis
RUN echo 'extension=redis.so' > /usr/local/etc/php/conf.d/redis.ini

RUN mkdir -p /var/www
ADD *.php /var/www

EXPOSE 9000
