# Notes
## Description

The Notes service functions as a platform for storing private notes. It offers various features such as registration, authentication, note addition, and site translation incorporation.

## Vulnerability

There is a vulnerability within the language change feature, allowing the injection of arbitrary content to be parsed via php wrappers through `parse_ini_file()`. Exploiting this vulnerability enables the retrieval of arbitary environment variables, revealing the secret key used to sign data in a user's JWT token. With this secret key, unauthorized access to the system as any user becomes possible.

To exploit this vulnerability, follow these steps:

1. Generate a payload (HOME=${SECRET};) using [php_filter_chain_generator](https://github.com/synacktiv/php_filter_chain_generator).
2. Insert the payload into `cookies['language']`.
3. Visit the site to obtain the environment variable `$SECRET`.
4. Generate a JWT token with payload `{'user_id': user_id}`.
5. Access the `/notes` page with the generated JWT token to retrieve the flag.


