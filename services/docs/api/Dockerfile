FROM ruby:3.2.2

RUN gem install sinatra -v 3.0.6 && \
    gem install puma -v 6.3.0 && \
    gem install pg -v 1.5.3 && \
    gem install redis -v 5.0.6

WORKDIR /app
