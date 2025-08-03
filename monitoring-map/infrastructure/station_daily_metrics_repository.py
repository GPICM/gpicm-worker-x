from infrastructure.database import get_connection
from datetime import datetime, time, timedelta


def get_online_station_metrics():
        
    db = get_connection()

    collection = db["station_daily_metrics"]

    now = datetime.now()
    ten_minutes_ago = now - timedelta(minutes=10)

    pipeline = [
        {
            "$match": {
                "lastRecordAt": { "$gte": ten_minutes_ago },    
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
                "latestWindDirection": 1,
                "lastedWindSpeed": 1,
                "stationSlug": 1
            }
        }
    ]

    print("Collection:", collection)
    print("Pipeline:", pipeline)

    results = collection.aggregate(pipeline)
    docs = list(results)

    return docs
