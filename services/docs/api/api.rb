#!/usr/bin/env ruby

require 'json'
require 'openssl'
require 'pg'
require 'redis'
require 'sinatra'

helpers do
  def db(user_name)
    redis = Redis.new(url: ENV["REDIS_URI"])
    connection_string = redis.get(user_name)
    PG.connect(connection_string)
  end

  def user_name(req)
    docs_session = req.cookies["docs_session"]
    user_name, split, origin_sign = docs_session.rpartition("--")
    sign = OpenSSL::HMAC.hexdigest("sha1", ENV["DOCS_SECRET"], user_name)
    if origin_sign != sign
      raise "Invalid session"
    end
    user_name
  end
end

get '/users' do
  begin
    db = db(user_name(request))
    res = db.exec("select id, login, org from users")
    res.to_a.to_json
  rescue => e
    e.message.to_json
  end
end

put '/users/:id' do |user_id|
  begin
    db = db(user_name(request))
    data = JSON.parse request.body.read

    res = db.exec(
      "update users \
      set org = '#{data["org"]}' \
      where id = '#{user_id}' \
      returning id, login, org"
    )
    res.to_a.to_json
  rescue => e
    e.message.to_json
  end
end

get '/docs' do
  begin
    db = db(user_name(request))
    res = db.exec(
      "select
        *, (select login || '@' || org as owner_login from users where id = owner) \
      from docs"
    )
    res.to_a.to_json
  rescue => e
    e.message.to_json
  end
end

post '/docs' do
  begin
    db = db(user_name(request))
    data = JSON.parse request.body.read

    res = db.exec(
      "insert into docs (title, shares) values \
      ('#{data["title"]}', '{#{data["shares"].join(",")}}') \
      returning *"
    )
    res.to_a.to_json
  rescue => e
    e.message.to_json
  end
end

put '/docs/:id' do |doc_id|
  begin
    db = db(user_name(request))
    data = JSON.parse request.body.read

    res = db.exec(
      "update docs set \
        title = '#{data["title"]}', \
        shares = '{#{data["shares"].join(",")}}' \
      where id = '#{doc_id}'
      returning *"
    )
    res.to_a.to_json
  rescue => e
    e.message.to_json
  end
end

get '/contents/:id' do |doc_id|
  begin
    db = db(user_name(request))
    res = db.exec(
      "select *
      from contents
      where doc_id = '#{doc_id}'"
    )
    res.to_a.to_json
  rescue => e
    e.message.to_json
  end
end

post '/contents' do
  begin
    db = db(user_name(request))
    data = JSON.parse request.body.read

    res = db.exec(
      "insert into contents (doc_id, data) values \
      ('#{data["doc_id"]}', '#{data["data"]}') \
      returning *"
    )
    res.to_a.to_json
  rescue => e
    e.message.to_json
  end
end
