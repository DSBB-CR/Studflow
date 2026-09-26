from pymongo import MongoClient
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent / ".env")

uri = os.getenv("MONGO_URI")
db_name = os.getenv("MONGO_DB", "studflow")

print("URI:", uri)
client = MongoClient(uri, serverSelectionTimeoutMS=5000)
try:
    client.admin.command("ping")
    print("✅ Подключение к Atlas OK")
    print("Коллекции:", client[db_name].list_collection_names())
except Exception as e:
    print("❌ Ошибка подключения:", e)