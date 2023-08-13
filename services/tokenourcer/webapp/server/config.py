import dataclasses
import os


@dataclasses.dataclass
class Config:
    redis_host: str


PROD_CONFIG = Config(
    redis_host='redis',
)


DEV_CONFIG = Config(
    redis_host='localhost',
)


def get_config():
    env = os.getenv('ENV', 'DEV')
    return {
        'DEV': DEV_CONFIG,
        'PROD': PROD_CONFIG,
    }[env]
