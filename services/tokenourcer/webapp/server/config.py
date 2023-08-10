import dataclasses
import os


@dataclasses.dataclass
class Config:
    redis_host: str
    postgres_host: str
    postgres_user: str
    postgres_db: str
    postgres_password: str


PROD_CONFIG = Config(
    redis_host='redis',
    postgres_host='postgres',
    postgres_user='postgres',
    postgres_db='postgres',
    postgres_password='mysecretpassword',
)


DEV_CONFIG = Config(
    redis_host='localhost',
    postgres_host='localhost',
    postgres_user='postgres',
    postgres_db='postgres',
    postgres_password='mysecretpassword',
)


def get_config():
    env = os.getenv('ENV', 'DEV')
    return {
        'DEV': DEV_CONFIG,
        'PROD': PROD_CONFIG,
    }[env]
