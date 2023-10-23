import os
import redis
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(verbose=True)
uri = os.getenv("ATLAS_URI")
client = MongoClient(uri)
db = client.ptt

TARGET_COLLECTION = "testing_collection"

redis_pool = redis.ConnectionPool(
    host=os.getenv("REDIS_HOST", "localhost"),
    port=os.getenv("REDIS_PORT", 6379),
    db=os.getenv("REDIS_DB", 1),
    password=os.getenv("REDIS_PASSWORD", None),
    socket_timeout=10,
    socket_connect_timeout=10,
)
redis_conn = redis.StrictRedis(connection_pool=redis_pool, decode_responses=True)

