import json
import numpy as np
import schedule
import time

from scipy.interpolate import Rbf
from shapely.geometry import Point, shape
from shapely import vectorized
from data.load_metrics import loadMetricDataFrames
from data.create_geojson import createGeojson
from data.kriging_interpolation import kriging_interpolation
from infrastructure.interpolated_maps_repository import upsert_interpolated_map

# Load config
with open("./config.json") as f:
    config_data = json.load(f)

# Build field config map
field_config_map = {}
for cfg in config_data.get("configures", []):
    field = cfg["field"]
    levels = cfg.get("levels", [])
    field_config_map[field] = {
        "limits": sorted(level["limit"] for level in levels),
        "colors": [level["color"] for level in levels],
        "interpolation": cfg.get("interpolation"),
    }
    if "min" in cfg:
        field_config_map[field]["min"] = cfg["min"]

def main():
    try:
        # Load GeoJSON borders
        print("Loading GeoJSON borders")
        with open("./macae.json") as f:
            border_geojson = json.load(f)

        hull_poly = shape(border_geojson["features"][0]["geometry"])
        hull_poly_simple = hull_poly.simplify(0.01, preserve_topology=True)

        # Load metrics
        print("Loading metric data")
        metric_dfs = loadMetricDataFrames(field_config_map)
        if not metric_dfs:
            print("No valid metric data available.")
            return

        for field, df in metric_dfs.items():
            print(f"\nProcessing field: {field} with {len(df)} points")

            config = field_config_map.get(field)
            if not config:
                print(f"⚠️  No config found for {field}, skipping.")
                continue

            points = df[['lon', 'lat']].values

            buffer = 0.05
            grid_lon = np.linspace(df['lon'].min() - buffer, df['lon'].max() + buffer, 150)
            grid_lat = np.linspace(df['lat'].min() - buffer, df['lat'].max() + buffer, 150)
            grid_x, grid_y = np.meshgrid(grid_lon, grid_lat)

            interpolation_method = config["interpolation"]
            print(f"Using interpolation method: {interpolation_method}")
            if interpolation_method == "kriging":
                z_interp = kriging_interpolation(df, field, grid_lon, grid_lat)
            elif interpolation_method == "rbf":
                rbf = Rbf(df['lon'], df['lat'], df[field], function='linear')
                z_interp = rbf(grid_x, grid_y)
            else:
                print(f"⚠️ Unsupported interpolation method: {interpolation_method}")
                continue

            if z_interp is None:
                print("Interpolation returned None")
                continue

            # Mask outside convex hull
            mask = np.zeros_like(grid_x, dtype=bool)
            for i in range(grid_x.shape[0]):
                for j in range(grid_x.shape[1]):
                    if not hull_poly_simple.contains(Point(grid_x[i, j], grid_y[i, j])):
                        mask[i, j] = True

            # mask = ~vectorized.contains(hull_poly_simple, grid_x, grid_y)
            z_interp[mask] = np.nan

            # Generate GeoJSON
            levels = config["limits"]
            colors = config["colors"]

            geojson = createGeojson(grid_x, grid_y, z_interp, levels, hull_poly_simple, colors)

            # Save to DB (or optionally to file)
            upsert_interpolated_map(field, geojson)

            #To Debug
                      
            #filename = f"contours_{field}.geojson"
            #with open(filename, 'w') as f:
            #    json.dump(geojson, f, indent=2)  
            print(f"Saved GeoJSON for {field}")
            print(f"Stations included: {len(points)}")
            print(f"Levels: {levels}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error:", e)

if __name__ == "__main__":
    print("Scheduler started. Running every 10 minutes.")
    schedule.every(10).minutes.do(main)
    main()
    try:
        while True:
            schedule.run_pending()
            time.sleep(10)
    except KeyboardInterrupt:
        print("Stopped by user.")