import os
from dotenv import load_dotenv


load_dotenv()


def get_mongo_uri() -> str:
    return os.getenv("MONGODB_URI", "mongodb://localhost:27017/")


def get_db_name() -> str:
    return os.getenv("MONGODB_DB", "twse")

