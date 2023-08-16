FROM nginx:1.25-alpine

# ./deploy_frontend.sh should be called first.
COPY frontend.build /var/www/html

COPY frontend.nginx.conf /etc/nginx/conf.d/default.conf
