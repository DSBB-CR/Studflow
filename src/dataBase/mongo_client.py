# dataBase/mongo_client.py
import os
from pymongo import MongoClient
from dotenv import load_dotenv

load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "studflow")

# Один клиент на всё приложение (pymongo потокобезопасен)
client = MongoClient(MONGO_URI)

db = client[MONGO_DB]

# Коллекции
universities_col   = db["universities"]
users_col          = db["users"]
counters_col       = db["counters"]
queries_col        = db["queries"]
dialog_states_col  = db["dialog_states"]
event_log_col      = db["event_log"]