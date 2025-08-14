import asyncio
from core.client import Client
from core.room import Room

async def main() -> None:
    search_criteria = {
		"peerSex": "MALE",
		"group": 0,
		"userAge": {
			"from": 0,
			"to": 17
		},
		"userSex": "FEMALE"
    }
    search_criteria2 = {
		"peerSex": "FEMALE",
		"group": 0,
		"userAge": {
			"from": 0,
			"to": 17
		},
		"userSex": "MALE"
    }
    client = Client(
        user_id="9a80c82b-6d0b-44e4-ac36-a7f55c242416",
        ua="Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
        search_criteria=search_criteria
    )
    client2 = Client(
        user_id="645881ef-c325-45cf-9dbb-ce6e325af4b4",
        ua="Mozilla/5.0 (X11; Linux x86_64; rv:141.0) Gecko/20100101 Firefox/141.0",
        search_criteria=search_criteria2
    )
    room = Room()
    room.add_member(client)
    room.add_member(client2)
    await asyncio.gather(
        client.connect(),
        client2.connect()
    )

asyncio.run(main())