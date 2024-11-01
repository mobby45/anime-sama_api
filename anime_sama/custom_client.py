from hashlib import blake2b

import hishel
import httpcore
from hishel._utils import normalized_url


def generate_key(request: httpcore.Request) -> str:
    encoded_url = normalized_url(request.url).encode("ascii")

    # Suppression de l'encodage de request.method
    key_parts = [
        request.method,  # Suppression de .encode("ascii") car c'est déjà en bytes
        encoded_url,
        b"" if request.stream is None else request.stream,  # Vérification de request.stream
    ]

    key = blake2b(digest_size=16)
    for part in key_parts:
        if isinstance(part, bytes):
            key.update(part)
        elif hasattr(part, "read"):  # Vérifie si l'objet est un flux de type fichier
            key.update(part.read())
    return key.hexdigest()


class CustomAsyncClient(hishel.AsyncCacheClient):
    def __init__(self, *args, **kwargs):
        customs = {
            "timeout": 30.0,
            "storage": hishel.AsyncFileStorage(ttl=3600),
            "controller": hishel.Controller(key_generator=generate_key),
        }
        customs.update(kwargs)

        super().__init__(*args, **customs)

    async def request(self, *args, **kwargs):
        if kwargs.get("extensions") is None:
            kwargs["extensions"] = {"force_cache": True}

        return await super().request(*args, **kwargs)
