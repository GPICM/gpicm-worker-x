from infrastructure.database import get_connection

def get_active_stations():
    db = get_connection()
    collection = db["stations"]

    pipeline = [
        {
            "$match": {
                "isActive": True
            }
        },
        {
            "$project": {
                "_id": 1,
                "geoPosition": 1,
            }
        }
    ]

    results = collection.aggregate(pipeline)
    return list(results)
