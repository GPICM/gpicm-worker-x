import pandas as pd

from infrastructure import station_daily_metrics_repository

fields = [
    "rainVolumeAcc",
    "latestWindGust",
    "latestWindSpeed",
    "latestTemperature",
    "latestWindDirection"
]

def loadMetricDataFrames():

    docs = list(station_daily_metrics_repository.get_online_station_metrics())
    base_data = []

    for doc in docs:

        geo = doc.get("geoPosition", {}).get("coordinates")
        if not geo or len(geo) != 2:
            continue
        
        dic = {
            "lon": geo[0],
            "lat": geo[1],
            "station": doc.get("stationSlug")
        }

        for field in fields:
            value = doc.get(field)
            dic[field] = value if isinstance(value, (int, float)) else None
        
        base_data.append(dic)

    # Convert to DataFrame for outlier detection
    full_df = pd.DataFrame(base_data)
    if full_df.empty:
        return {}
    
        # Filter out rows with all metrics missing
    full_df = full_df.dropna(subset=fields, how="all")

    # Generate one DataFrame per field
    field_dfs = {}

    for field in fields:
        df = full_df[["lon", "lat", "station", field]].dropna(subset=[field])

        if df.empty:
            continue

        # IQR outlier filtering
        Q1 = df[field].quantile(0.25)
        Q3 = df[field].quantile(0.75)
        IQR = Q3 - Q1
        lower = Q1 - 1.5 * IQR
        upper = Q3 + 1.5 * IQR

        df = df[(df[field] >= lower) & (df[field] <= upper)]

        field_dfs[field] = df.reset_index(drop=True)

    return field_dfs