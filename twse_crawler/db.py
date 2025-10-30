from typing import Iterable, List, Dict, Any
from pymongo import MongoClient, UpdateOne
from pymongo.collection import Collection
from .config import get_mongo_uri, get_db_name


_client: MongoClient | None = None


def _get_client() -> MongoClient:
    global _client
    if _client is None:
        _client = MongoClient(get_mongo_uri())
    return _client


def get_collection(name: str) -> Collection:
    db = _get_client()[get_db_name()]
    return db[name]


def ensure_indexes() -> None:
    t86 = get_collection("t86")
    t86.create_index([("date", 1), ("stock_code", 1)], unique=True)

    bfi82u = get_collection("bfi82u")
    bfi82u.create_index([("date", 1)], unique=True)


def upsert_t86(docs: Iterable[Dict[str, Any]]) -> int:
    coll = get_collection("t86")
    ops: List[UpdateOne] = []
    for d in docs:
        key = {"date": d["date"], "stock_code": d.get("stock_code")}
        ops.append(UpdateOne(key, {"$set": d}, upsert=True))
    if not ops:
        return 0
    res = coll.bulk_write(ops, ordered=False)
    # inserted + upserted + modified (counting as success)
    return (res.upserted_count or 0) + (res.modified_count or 0)


def upsert_bfi82u(doc: Dict[str, Any]) -> None:
    coll = get_collection("bfi82u")
    coll.update_one({"date": doc["date"]}, {"$set": doc}, upsert=True)

