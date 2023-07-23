from environs import Env

env = Env()
env.read_env()  # read .env file, if it exists


DO_API_TOKEN = env.str("DO_API_TOKEN")

MOT_D_POSTLUDE = """HITB SECCONF CTF 2023, ctf@hitb.org
https://2023.ctf.hitb.org/hitb-ctf-phuket-2023"""

CERTIFICATES_FOLDER = env.path("CERTIFICATES_FOLDER", "../../certificates")

teams1_100_ctf_hitb_org = CERTIFICATES_FOLDER / "team1.ctf.hitb.org"
teams101_200_ctf_hitb_org = CERTIFICATES_FOLDER / "team101.ctf.hitb.org"
PROXY_CERTIFICATES = {
    "wildcard.ctf.hitb.org": {
        tuple(range(1, 101)): (teams1_100_ctf_hitb_org / "fullchain1.pem", teams1_100_ctf_hitb_org / "privkey1.pem"),
        tuple(range(101, 201)): (teams101_200_ctf_hitb_org / "fullchain1.pem", teams101_200_ctf_hitb_org / "privkey1.pem"),
    },
}
PROXY_SSH_KEY = env.path("PROXY_SSH_KEY", "../ctf-cloud/cloud/cloud_master/files/api_srv/do_deploy_key")
PROXY_SSH_PORT = env.int("PROXY_SSH_PORT", 2222)
PROXY_SSH_USERNAME = env.str("PROXY_SSH_USERNAME", "root")

BASE_TEAM_NETWORK = env.str("BASE_TEAM_NETWORK", "10.60.0.0/14")
TEAM_NETWORK_MASK = env.int("TEAM_NETWORK_MASK", 24)

DNS_ZONE = env.str("DNS_ZONE", "ctf.hitb.org")

TEAMS_COUNT = 118
PROXY_HOSTS = {
    team_id: f"10.80.{team_id}.2" for team_id in range(1, TEAMS_COUNT + 1)
}
