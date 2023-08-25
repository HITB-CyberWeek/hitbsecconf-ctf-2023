# Tokenourcer
## Description
Tokenourcer is a service for managing resources with token-based access. Service has the following entities:

`token_name` - token public part, can be used for sharing resources

`token_secret` - token secret part, using for the authorization

`resource` - secret data. Every resource has a counter with access statistics.

There are tables for managing access to resources: `token_to_resources` and `resource_to_tokens` with access maps. `resource_to_tokens` keeps tokens **list** by resource id. Token with index 0 is always an owner token, it's need to keep it as list for the denoting an owner. 
`token_to_resources` keeps resource ids **set** (there is no need to denote owner and keep it as a list) by token.

You can share access for the resource to another token by its name.

## Vulnerability

1. Static serving config has an [nginx alias misconfiguration](https://github.com/HITB-CyberWeek/hitbsecconf-ctf-2023/blob/main/services/tokenourcer/nginx.conf#L10), which gives an opportunity to steal the logs in this way: `curl "https://<hostname>/assets../logs/app.error.log"`.
2. If you grant access to a resource twice, and then revoke twice, this will lead to the record deletion from `token_to_resources` and [counter deletion](https://github.com/HITB-CyberWeek/hitbsecconf-ctf-2023/blob/main/services/tokenourcer/webapp/server/storage_api.py#L157), but record in `resource_to_token` won't be deleted. So if user try to get this resource, it will pass all [existence checks](https://github.com/HITB-CyberWeek/hitbsecconf-ctf-2023/blob/main/services/tokenourcer/webapp/server/main.py#L138) (because the are based on the `resource_to_token` map), but fail at [the counter record check](https://github.com/HITB-CyberWeek/hitbsecconf-ctf-2023/blob/main/services/tokenourcer/webapp/server/storage_api.py#L58) with KeyError with full token as key and log it to `app.error.log`.

## Attack

Exploitation plan:

1. Create a "hacker" resource
2. Give access to this resource twice by victim token's name
3. Revoke access to this resource twice by victim token's name
4. Wait until checksystem get this resource (it can be checked by an error 500 in the access.log)
5. "Fix" this resource by granting access to this resource. It will add record to `token_to_resources`, so getting the resource won't raise a KeyError
6. Get user resource_id by matching `resource_id` and `token_secret` in `access.log` and `app.error.log` correspondingly
7. Get resource data with victim token_secret as usual

## Defense

1. Fix nginx alias misconfiguration
2. Get rid of asymmetry in `token_to_resources` and `resource_to_tokens` maps and / or change token ownership's management
