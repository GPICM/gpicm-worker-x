from datetime import datetime, timezone
from infrastructure.database import get_connection

import gzip
import json
import base64

def compress_geojson(geojson: dict) -> str:
    """Compress GeoJSON using gzip and encode as base64 string."""
    json_bytes = json.dumps(geojson).encode('utf-8')
    compressed = gzip.compress(json_bytes)
    return base64.b64encode(compressed).decode('utf-8')

def round_to_10min(dt: datetime) -> datetime:
    """Round a datetime to the nearest 10-minute block."""
    return dt.replace(minute=(dt.minute // 10) * 10, second=0, microsecond=0)

def upsert_interpolated_map(
    field: str,
    contour_geojson: dict,
    generation_time: datetime = None,
):
    
    if generation_time is None:
        generation_time = datetime.now(timezone.utc)

    interval = round_to_10min(generation_time)

    db = get_connection()
    collection = db["interpolated_maps"]

    doc = {
        "field": field,
        "interval": interval,
        "timestamp": generation_time,
        "geojson_compressed": compress_geojson(contour_geojson)
    }

    collection.update_one(
        {"field": field, "interval": interval},
        {"$set": doc},
        upsert=True
    )

    print(f"Upserted contour map for field '{field}' at {interval.isoformat()}")
