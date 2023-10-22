import os
from dotenv import load_dotenv
from pymongo import MongoClient

load_dotenv(verbose=True)
uri = os.getenv("ATLAS_URI")
client = MongoClient(uri)
db = client.ptt

TARGET_COLLECTION = "testing_collection"
