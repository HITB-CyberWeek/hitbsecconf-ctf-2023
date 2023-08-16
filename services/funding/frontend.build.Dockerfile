FROM node:20-alpine AS build

WORKDIR /app/

COPY frontend/package*.json ./

RUN npm ci

COPY frontend /app/frontend
COPY ethereum /app/ethereum

WORKDIR /app/frontend

RUN cp next.config.js.production next.config.js

CMD npm run build
