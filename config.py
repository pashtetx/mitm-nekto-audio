from configparser import ConfigParser
from typing import Generator, Union, Optional
from core.client import Client
from pathlib import Path

def get_discord_config(path: Union[str, Path] = "config.ini") -> Optional[dict]:
    config = ConfigParser()
    config.read(path)
    token = config.get("discord", "discord-token", fallback=None)
    reconnect = config.getboolean("discord", "reconnect-after-dialog", fallback=False)
    reconnect_delay = config.getfloat("discord", "reconnect-delay", fallback=5.0)
    return {
        "token":token,
        "reconnect":reconnect,
        "reconnect_delay":reconnect_delay,
    }

def parse_clients_config(path: Union[str, Path] = "config.ini") -> Generator[Client, None, None]:
    config = ConfigParser()
    config.read(path)
    names_of_clients = config.get("settings", "clients")
    for name in names_of_clients.replace(" ", "").split(","):
        option = f"client/{name}"
        user_id = config.get(option, "user_id")
        ua = config.get(option, "ua")
        user_sex = config.get(option, "sex", fallback=None)
        search_sex = config.get(option, "search-sex", fallback=None)
        user_age = config.get(option, "age", fallback=None)
        search_age = config.get(option, "search-age", fallback=None)
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
            user_id=user_id,
            ua=ua,
            search_criteria=criteria
        )

discord_config = get_discord_config()