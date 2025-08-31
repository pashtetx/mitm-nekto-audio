from socketio import AsyncClient

class Transport(AsyncClient):
    
    endpoint = "wss://audio.nekto.me/"

    async def connect(self, ua: str, wait: bool = True) -> None:
        await super().connect(

        )
        if wait:
            await super().wait()