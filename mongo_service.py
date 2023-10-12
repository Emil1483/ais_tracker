from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from helpers import string_to_object_id
import os


class DuplicateException(Exception):
    pass


load_dotenv()

client = MongoClient(os.getenv("MONGO_URL"))
db = client["ais_tracker"]
movements_collection = db["movements"]


def insert_movement(name: str, mmsi: int, from_pos: dict, to_pos: dict):
    vessel_data = {
        "_id": string_to_object_id(str(mmsi)),
        "name": name,
        "mmsi": mmsi,
        "from_position": from_pos,
        "to_position": to_pos,
    }

    try:
        movements_collection.insert_one(vessel_data)
    except DuplicateKeyError:
        raise DuplicateException()


def get_movements():
    def gen():
        for movement in movements_collection.find():
            movement["_id"] = str(movement.get("_id"))
            yield movement

    return [*gen()]
