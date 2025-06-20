import os
import redis
import json
from dotenv import load_dotenv

load_dotenv()
class RedisHandler:
    def __init__(self,
                hostname: str=os.environ.get("REDIS_HOST"),
                username: str=os.environ.get("REDIS_USER"),
                password: str=os.environ.get("REDIS_PASS"),
                port: int=os.environ.get("REDIS_PORT"),
                decode_responses: bool = True
                ):
        self._connection = redis.Redis(host=hostname,
                                       username=username,
                                       password=password,
                                       port=port,
                                       decode_responses=decode_responses,
                                       ssl=True,
                                       )

    def set_kv_data(self, key: str, val: dict, expiry: int = None) -> None:
        val = json.dumps(val)
        self._connection.set(key, val)
        if expiry:
            self._connection.expire(key, expiry)

    def read_kv(self, key: str) -> str:
        val = self._connection.get(key)
        if val is not None:
            val = json.loads(val)
        return val


    def close_connection(self):
        self._connection.close()
