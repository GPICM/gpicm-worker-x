from data.database import get_today_online_station_metrics

def loadMetrics(field="latestTemperature"):
        
    docs = list(get_today_online_station_metrics())

    df = []

    for i in range(0, len(docs)):
        doc = docs[i]

        dic = {
            "lon": doc.get("geoPosition").get("coordinates")[0],
            "lat": doc.get("geoPosition").get("coordinates")[1],
            "value": doc.get(field),
            "station": doc.get("stationSlug")
        }
        df.append(dic)

    return df
