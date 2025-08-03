import pandas as pd

from infrastructure import station_daily_metrics_repository

def apply_local_iqr(df: pd.DataFrame, field: str, cell_size: float = 0.1, min_value: float | None = None ) -> pd.DataFrame:

    if df.empty or df[field].isnull().all():
        return df

    df = df.copy()
    df["cell_x"] = (df["lon"] / cell_size).astype(int)
    df["cell_y"] = (df["lat"] / cell_size).astype(int)

    def iqr_filter(group):

        cx, cy = group.cell_x.iloc[0], group.cell_y.iloc[0]
        values = group[field].tolist()

        print(f"\n[GRUPO] Célula ({cx}, {cy}) — {len(group)} pontos")
        print(f"Valores: {values}")

        if len(group) < 4:
            print(f" Dados insuficientes para aplicar IQR — mantendo todos os pontos")
            kept = group
        else:
            Q1 = group[field].quantile(0.25)
            Q3 = group[field].quantile(0.75)
            IQR = Q3 - Q1
            lower = Q1 - 1.5 * IQR
            upper = Q3 + 1.5 * IQR

            print(f"🔢 Q1: {Q1:.2f}, Q3: {Q3:.2f}, IQR: {IQR:.2f}")
            print(f"📐 Limites: [{lower:.2f}, {upper:.2f}]")

            outliers = group[(group[field] < lower) | (group[field] > upper)]
            kept = group[(group[field] >= lower) & (group[field] <= upper)]

            print(f"✅ Mantidos: {len(kept)} | 🗑️ Removidos: {len(outliers)}")

            if not outliers.empty:
                print(f"🗑️  Valores removidos: {outliers[field].tolist()}")

        # Se min_value foi informado, remove valores abaixo dele
        if min_value is not None:
            below_min = kept[kept[field] < min_value]
            kept = kept[kept[field] >= min_value]

            if not below_min.empty:
                print(f"Removidos por estarem abaixo do mínimo ({min_value}): {below_min[field].tolist()}")

        return kept
    
    grouped = df.groupby(["cell_x", "cell_y"], group_keys=False)
    filtered = grouped[[field, "lon", "lat", "station", "cell_x", "cell_y"]].apply(iqr_filter)

    filtered = filtered.drop(columns=["cell_x", "cell_y"]).reset_index(drop=True)

    if filtered.empty:
        print(f"[IQR] Todos os dados de '{field}' foram removidos após o filtro.")

    return filtered

fields = [
    "latestTemperature",
    "latestAtmosphericPressure",
    "latestThermalSensation",

    "latestWindGust",
    "latestWindSpeed",

    "rainVolumeAcc",
    "latestRainVolume",
]

def loadMetricDataFrames(field_config_map: dict):

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

        print(f"[IQR] Antes do filtro: {len(df)} linhas")

        # Get min_value for this field if available
        min_value = None
        config = field_config_map.get(field)

        if config and "min" in config:
            min_value = config["min"]
        
        df = apply_local_iqr(df, field, cell_size=0.1, min_value=min_value)

        print(f"[IQR] Após o filtro: {len(df)} linhas")

        if not df.empty:
            field_dfs[field] = df.reset_index(drop=True)

    return field_dfs



