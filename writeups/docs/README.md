# Docs

## Description

Docs is a simple web service which allows:
- register/login new user
- get list of users with org's information
- get list of documents
- create a new document and share it with other users
- create/get content of documents

Docs consits of next services:
- auth service written in Python
    - create new user in service and Pg and save connection strings in Redis database
- api service written in Ruby
- PostgreSQL
- Redis

## Vuln

There is no any filters or checking input in api [service](../../services/docs/api/api.rb), so we have an SQL injection. But we can't directly get data from `contents` table because of row level security: we can see only own content or content of documents which was shares we us. Firstly we need to share needed documents to us via SQL injection and then just get a content via API.

See details in [sploit](../../sploits/docs/sploit.py).
