from infrastructure.database import get_connection
from datetime import datetime, timedelta


def get_online_station_metrics(date: datetime = None):
        
    db = get_connection()
    collection = db["station_daily_metrics"]

    match_filter = {}

    if date is None:
        # No date passed, filter lastRecordAt >= now - 10 minutes
        ten_minutes_ago = datetime.now() - timedelta(minutes=10)
        match_filter["lastRecordAt"] = { "$gte": ten_minutes_ago }
    else:
        # Filter records that happened on the given date (ignore time)
        start_of_day = datetime(date.year, date.month, date.day)

        end_of_day = start_of_day + timedelta(days=1)

        match_filter["lastRecordAt"] = {
            "$gte": start_of_day,
            "$lt": end_of_day
        }

    pipeline = [
        {
            "$match": match_filter
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
                "stationSlug": 1,
                "geoPosition": "$stationData.geoPosition",
                "latestTemperature": 1,
                "rainVolumeAcc": 1,
                "latestWindGust": 1,
                "lastedWindSpeed": 1,
                "minTemperature": 1,
                "latestAtmosphericPressure": 1,
                "latestThermalSensation": 1,
                "latestWindSpeed": 1,
                "latestRainVolume": 1,
                "latestAirHumidity": 1
            }
        }
    ]

    print("Collection:", collection)
    print("Pipeline:", pipeline)

    results = collection.aggregate(pipeline)
    docs = list(results)

    return docs
