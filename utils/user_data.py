from dotenv import load_dotenv
import os
from pymongo import MongoClient

load_dotenv()

client = MongoClient(os.getenv("MONGO_URI"))
db = client["Fincov_user_data"]

def extract_user_data(phone: str):
    query = [
        {"$match": {"phone": phone}},
        {
            "$lookup": {
                "from": "accounts",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "accounts"
            }
        },
        {
            "$lookup": {
                "from": "transactions",
                "let": {"accountIds": "$accounts._id"},
                "pipeline": [
                    {"$match": {"$expr": {"$in": ["$account_id", "$$accountIds"]}}}
                ],
                "as": "transactions"
            }
        },
        {
            "$lookup": {
                "from": "loans",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "loans"
            }
        },
        {
            "$lookup": {
                "from": "investments",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "investments"
            }
        },
        {
            "$lookup": {
                "from": "insurances",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "insurances"
            }
        },
        {
            "$lookup": {
                "from": "taxes",
                "localField": "_id",
                "foreignField": "user_id",
                "as": "taxes"
            }
        }
    ]

    result = list(db.users.aggregate(query))
    
    return result[0] if result else None
