FROM node:20-alpine AS build

WORKDIR /app/

# RUN apk add --no-cache python3 make g++ # Needed for building Node-gyp

COPY frontend/package*.json ./

RUN npm ci

COPY . .

WORKDIR /app/frontend/

RUN cp next.config.js.production next.config.js

RUN npm run build

FROM nginx:1.25-alpine

COPY --from=build /app/frontend/out /var/www/html

COPY frontend/nginx.conf /etc/nginx/conf.d/default.conf
