FROM nginx:1.25.2-alpine

RUN apk update
RUN apk add logrotate

ADD logrotate.conf /etc/logrotate.d/nginx
RUN chown root:root /etc/logrotate.d/nginx
RUN chmod a-w /etc/logrotate.d/nginx
