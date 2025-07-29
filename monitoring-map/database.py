import os

from pymongo import MongoClient
from datetime import datetime, time, timedelta

# Connect to local MongoDB

DATABASE_URL = os.getenv("DATABASE_URL")

client = MongoClient(DATABASE_URL)
db = client["weather"]
collection = db["station_daily_metrics"]


def get_today_online_station_metrics():
        
    now = datetime.now()
    start_today = datetime.combine(now.date(), time.min)  # 00:00:00 hoje
    end_today = datetime.combine(now.date(), time.max)    # 23:59:59.999999 hoje

    pipeline = [

        {
            "$match": {
                "isOnline": True,
                "date": { "$gte": start_today, "$lte": end_today },
                "latestTemperature": { "$ne": None }
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
                "latestThermalSensation": 1,
                "latestWindGust": 1,
                "stationSlug": 1
            }
        }
    ]

    results = collection.aggregate(pipeline)
    docs = list(results)

    return docs



""" if __name__ == "__main__":
    DATABASE_URL = "mongodb://lucasfonseca:fsJpN33iAW9r@10.77.0.26:27017/?authSource=admin"
    client = MongoClient(DATABASE_URL)
    db = client["weather"]
    collection = db["station_daily_metrics"]

    results = get_today_online_station_metrics(collection)
    print("Documentos hoje:", results) """