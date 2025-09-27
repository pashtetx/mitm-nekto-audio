from configparser import ConfigParser
from typing import Generator, Union, Optional
from core.client import Client
from pathlib import Path

from functools import partial

def safe_get(config: ConfigParser, section: str, key: str) -> None:
    return config.get(section, key, fallback=None)

def get_config(path: Union[str, Path] = "config.ini") -> Optional[dict]:
    config = ConfigParser()
    config.read(path)
    return config

def parse_clients_config(path: Union[str, Path] = "config.ini") -> Generator[Client, None, None]:
    config = get_config(path=path)
    names_of_clients = config.get("settings", "clients")
    for name in names_of_clients.replace(" ", "").split(","):
        option = f"client/{name}"
        user_id = config.get(option, "user_id")
        ua = config.get(option, "ua")
        user_sex = config.get(option, "sex", fallback=None)
        search_sex = config.get(option, "search-sex", fallback=None)
        user_age = config.get(option, "age", fallback=None)
        search_age = config.get(option, "search-age", fallback=None)
        wait_for = config.get(option, "wait-for", fallback=None)
        criteria = {
            "group":0,
        }
        if user_sex: criteria["userSex"] = user_sex
        else: criteria["userSex"] = "ANY"
        if search_sex: criteria["peerSex"] = search_sex
        else: criteria["peerSex"] = "ANY"
        if user_age: 
            criteria["userAge"] = {
                "from":user_age.split(",")[0],
                "to":user_age.split(",")[1]
            }
        if search_age:
            criteria["peerAges"] = [
                {
                    "from":age.split(",")[0],
                    "to":age.split(",")[1],
                } 
                for age in search_age.split("-")
            ]
        yield Client(
            name=name,
            user_id=user_id,
            ua=ua,
            search_criteria=criteria,
            wait_for=wait_for
        )

_discord_config = get_config()
load_discord = partial(_discord_config.get, "discord")
bool_load_discord = partial(_discord_config.getboolean, "discord", fallback=False)
load_safe_discord = partial(_discord_config.get, "discord", fallback=None)
