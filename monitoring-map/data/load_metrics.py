import pandas as pd

from infrastructure import station_daily_metrics_repository

def loadMetrics(field="latestWindDirection"):
    docs = list(station_daily_metrics_repository.get_online_station_metrics())
    data = []

    for doc in docs:
        val = doc.get(field)
        # Skip docs where value is None or not numeric
        if val is None or not isinstance(val, (int, float)):
            continue

        dic = {
            "lon": doc.get("geoPosition").get("coordinates")[0],
            "lat": doc.get("geoPosition").get("coordinates")[1],
            "value": val,
            "station": doc.get("stationSlug")
        }
        data.append(dic)

    # Convert to DataFrame for outlier detection
    df = pd.DataFrame(data)

    if df.empty:
        return []

    # IQR method for outlier detection on 'value'
    Q1 = df['value'].quantile(0.25)
    Q3 = df['value'].quantile(0.75)
    IQR = Q3 - Q1
    lower_bound = Q1 - 1.5 * IQR
    upper_bound = Q3 + 1.5 * IQR


    # Filter out outliers
    df_filtered = df[ (df['value'] != None) & (df['value'] >= lower_bound) & (df['value'] <= upper_bound)]

    # Return filtered data as list of dicts
    return df_filtered.to_dict(orient='records')
