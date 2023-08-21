FROM node:20-alpine AS compile-ethereum

WORKDIR /app/ethereum

COPY ethereum/package*.json ./

RUN npm ci

COPY ethereum /app/ethereum

RUN npm run compile


FROM node:20-alpine

WORKDIR /app/

COPY frontend/package*.json ./

RUN npm ci

COPY frontend /app/frontend
COPY --from=compile-ethereum /app/ethereum /app/ethereum

WORKDIR /app/frontend

RUN cp next.config.js.production next.config.js

ENV NODE_ENV=production

CMD npm run build
