import api
import generators

hostname = 'localhost'

user_token_name = generators.gen_token_name()
token_secret = api.issue_token(hostname, user_token_name)
print('token_secret:', token_secret)
resource_id = api.create_resource(hostname, token_secret, 'some content')
print('resource_id:', resource_id)
resource_ids = api.list_resources(hostname, token_secret)
print('resource_ids:', resource_ids)
resource_blob = api.get_resource(hostname, token_secret, resource_id)
print('resource_blob:', resource_blob)

hacker_token_name = 'hacker_' + generators.gen_token_name()
print(hacker_token_name)
hacker_token_secret = api.issue_token(hostname, hacker_token_name)
print('hacker_token_secret:', hacker_token_secret)
hacker_resource_id = api.create_resource(hostname, hacker_token_secret, 'hacker blob')
api.grant_access(hostname, hacker_token_secret, user_token_name, hacker_resource_id)
api.grant_access(hostname, hacker_token_secret, user_token_name, hacker_resource_id)

hacker_resource_blob = api.get_resource(hostname, token_secret, hacker_resource_id)
print('hacker_resource_blob:', hacker_resource_blob)

api.revoke_access(hostname, hacker_token_secret, user_token_name, hacker_resource_id)
api.revoke_access(hostname, hacker_token_secret, user_token_name, hacker_resource_id)

try:
    resource_blob = api.get_resource(hostname, token_secret, resource_id)
    print('resource_blob:', resource_blob)
except Exception:
    pass

api.grant_access(hostname, hacker_token_secret, user_token_name, hacker_resource_id)
resource_blob = api.get_resource(hostname, token_secret, resource_id)
print('resource_blob:', resource_blob)
