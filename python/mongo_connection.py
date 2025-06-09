from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

mongo_connection_string = os.getenv("MONGO_CONNECTION_STRING")

client = MongoClient(mongo_connection_string)


# this finally works
