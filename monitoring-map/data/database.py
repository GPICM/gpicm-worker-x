import os

from pymongo import MongoClient
from datetime import datetime, time, timedelta


DATABASE_URL = os.getenv("DATABASE_URL")
client = MongoClient(DATABASE_URL)
db = client["weather"]
collection = db["station_daily_metrics"]

def get_today_online_station_metrics():
        
    now = datetime.now()
    ten_minutes_ago = now - timedelta(minutes=10)

    pipeline = [
        {
            "$match": {
                "lastRecordAt": { "$gte": ten_minutes_ago },
                "latestTemperature": {
                    "$ne": None,
                    "$exists": True
                }          
            }
        },
        {
            "$sort": { "date": -1 }
        },
        {
            "$lookup": {
                "from": "stations",                
                "localField": "stationSlug",      
                "foreignField": "slug",           
                "as": "stationData"                
            }
        },
        {
            "$unwind": "$stationData"
        },
        {
            "$project": {
                "_id": 1,
                "geoPosition": "$stationData.geoPosition",
                "latestTemperature": 1,
                "rainVolumeAcc": 1,
                "latestWindGust": 1,
                "stationSlug": 1
            }
        }
    ]

    print("Collection:", collection)
    print("Pipeline:", pipeline)

    results = collection.aggregate(pipeline)
    docs = list(results)

    return docs
