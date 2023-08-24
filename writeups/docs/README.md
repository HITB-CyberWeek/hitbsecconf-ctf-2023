# docs

## Overview

The "Docs" web service is designed to facilitate various functions, including:
- Registering and logging in new users
- Retrieving a list of users along with organization information
- Accessing a list of documents
- Creating new documents and sharing them with other users
- Creating and obtaining document content

The system is composed of the following components:
- An authentication service coded in Python. This service creates new user records within the service and PostgreSQL, while storing connection strings in a Redis storage
- An API service written in Ruby
- PostgreSQL as a storage
- Redis for storing connection strings

## Vulnerability

The API service, as you can see in the [source code](../../services/docs/api/api.rb), lacks input filters or checks, rendering it susceptible to SQL injection attacks. However, direct access to data in the `contents` table is obstructed by [row-level security](https://www.postgresql.org/docs/current/ddl-rowsecurity.html). This means we can only view our own content or content from documents that have been shared with us. To exploit this, we must initially use SQL injection to share specific documents with us and subsequently retrieve their content via the API.

For a detailed walkthrough, refer to the [exploit](../../sploits/docs/sploit.py) provided.
