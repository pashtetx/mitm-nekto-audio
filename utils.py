import hashlib
import base64

def alarm(user_id: str, internal_id: int) -> str:
    payload = user_id + "BYdKPTYYGZ7ALwA" + "8oNm2" + str(internal_id)
    return base64.b64encode(
        hashlib.sha256(payload.encode())
        .hexdigest().encode()
    ).decode()