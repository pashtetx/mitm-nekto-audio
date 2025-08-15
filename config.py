from configparser import ConfigParser
from typing import Generator, Union
from core.client import Client
from pathlib import Path

def parse_clients_config(path: Union[str, Path] = "config.ini") -> Generator[Client]:
    config = ConfigParser()
    config.read(path)
    names_of_clients = config.get("settings", "clients")
    for name in names_of_clients.replace(" ", "").split(","):
        option = f"client/{name}"
        user_id = config.get(option, "user_id")
        ua = config.get(option, "ua")
        user_sex = config.get(option, "sex")
        search_sex = config.get(option, "search-sex")
        user_age = config.get(option, "age")
        search_age = config.get(option, "search-age")
        criteria = {
            "userSex":user_sex,
            "peerSex":search_sex,
            "peerAge":[
                {"from":age.split(",")[0],"to":age.split(",")[1],} for age in search_age.split("-")
            ],
            "userAge":{"from":user_age.split(",")[0],"to":user_age.split(",")[1],},
            "group":0,
        }
        yield Client(
            user_id=user_id,
            ua=ua,
            search_criteria=criteria
        )