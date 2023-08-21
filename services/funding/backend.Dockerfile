FROM node:20-alpine AS compile-ethereum

WORKDIR /app/ethereum

COPY ethereum/package*.json ./

RUN npm ci

COPY ethereum /app/ethereum

RUN npm run compile


FROM node:20-alpine

WORKDIR /app/

RUN apk update && \
    apk add --no-cache python3 make g++ bash # Needed for building Node-gyp

COPY backend/package*.json ./

RUN npm ci

COPY backend /app/backend
COPY --from=compile-ethereum /app/ethereum /app/ethereum

WORKDIR /app/backend/

ENV NODE_ENV=production

RUN npm run build:ts

CMD [ "/bin/bash", "-c", "npm run generate-key; npm run start" ]
