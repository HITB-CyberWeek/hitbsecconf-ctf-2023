FROM node:20.5.1
WORKDIR /app
COPY ./package.json .
RUN npm install
COPY ./index.js ./db.js /middlewares.js passportConfig.js .
COPY ./views views
COPY ./routes routes
COPY ./models models

USER node
EXPOSE 3000
CMD ["node", "index.js"]
