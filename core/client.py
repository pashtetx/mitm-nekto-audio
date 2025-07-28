from .dispatcter import Dispatcher

class Client:
    def __init__(self, token: str) -> None:
        dispatcher = Dispatcher()
