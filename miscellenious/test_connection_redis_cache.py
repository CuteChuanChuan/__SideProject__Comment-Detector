import os
import redis
from dotenv import load_dotenv

load_dotenv(verbose=True)

r = redis.Redis(host=os.getenv("REDIS_HOST"), port=os.getenv("REDIS_PORT"), db=os.getenv("REDIS_DB"))
print(r.ping())

r.set("foo", "bar")