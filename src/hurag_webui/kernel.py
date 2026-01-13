import yaml
import httpx
import logging

from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path.cwd() / ".webui.env")

from functools import lru_cache

class Tree:
    def __init__(self, data: dict):
        for key, value in data.items():
            if isinstance(value, dict):
                setattr(self, key, Tree(value))
            else:
                setattr(self, key, value)

    def __repr__(self):
        return f"{self.__dict__}"

@lru_cache(maxsize=1)
def conf():
    user_config_path = Path.cwd() / "webui-config.yaml"
    user_config = {}
    if user_config_path.exists() and user_config_path.is_file():
        with open(user_config_path, "r", encoding="utf-8") as f:
            user_config = yaml.safe_load(f) or {}

    return Tree(user_config)


@lru_cache(maxsize=1)
def logger():
    logger = logging.getLogger("hurag2_webui")
    logger.propagate = False
    logger.setLevel(logging.DEBUG)
    fmt = logging.Formatter(
        "%(asctime)s [%(name)s] %(levelname)s - %(message)s"
    )
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(fmt)
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    return logger

@lru_cache(maxsize=1)
async def root_org():

    async with httpx.AsyncClient(timeout=30) as aclient:
        resp = await aclient.get(conf().api.url + "/v1/info/organization")
        org = resp.json()

    return org["messages"][0]

