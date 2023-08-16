FROM node:20-alpine

WORKDIR /app/

RUN apk update && \
    apk add --no-cache python3 make g++ bash # Needed for building Node-gyp

COPY backend/package*.json ./

RUN npm ci

COPY backend /app/backend
COPY ethereum /app/ethereum

WORKDIR /app/backend/

RUN npm run build:ts

CMD [ "/bin/bash", "-c", "npm run generate-key; npm run start" ]
