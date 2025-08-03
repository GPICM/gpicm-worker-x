import os
from dotenv import load_dotenv
from pymongo import MongoClient

""" print("Loading environment variables")
load_dotenv() """

DATABASE_URL = os.getenv("MONGO_DB_URI")

_client = MongoClient(DATABASE_URL)
_db = _client["weather"]

def get_connection():
    return _db
