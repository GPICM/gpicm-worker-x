
import json
import numpy as np
import pandas as pd

from scipy.interpolate import Rbf
from shapely.geometry import Point, shape
from data.load_metrics import loadMetricDataFrames
from data.create_geojson import createGeojson

# Example: load your config JSON from file or string
with open("./monitoring-map/config.json") as f:
    config_data = json.load(f)

# Build a dict: field name -> sorted list of limits
levels_map = {}
colors_map = {}


for cfg in config_data.get("configures", []):
    field = cfg["field"]
    # Extract all limits from the "levels" list
    limits = [level["limit"] for level in cfg.get("levels", [])]
    # Sort ascending just in case
    limits = sorted(limits)
    levels_map[field] = limits

for cfg in config_data.get("configures", []):
    field = cfg["field"]
    colors = [level["color"] for level in cfg.get("levels", [])]
    colors_map[field] = colors

# Example output
print(levels_map)

def main():

    try:
        """ Load GeoJSON Borders """
    
        print("Loading Default GeoJson borders")
        with open("./monitoring-map/macae.json") as f:
            border_geojson = json.load(f)

        hull_poly = shape(border_geojson["features"][0]["geometry"])
        hull_poly_simple = hull_poly.simplify(0.01 , preserve_topology=True)


        """ Load Metric DataFrames """

        print("Loading Metrics")
        metric_dfs = loadMetricDataFrames()  # new function returning dict of dfs

        if not metric_dfs:
            print("No valid metric data available.")
            return
        
        for field, df in metric_dfs.items():
            print(f"Processing field: {field} with {len(df)} points")

            points = df[['lon', 'lat']].values

            buffer = 0.05
            grid_lon = np.linspace(df['lon'].min() - buffer, df['lon'].max() + buffer, 150)
            grid_lat = np.linspace(df['lat'].min() - buffer, df['lat'].max() + buffer, 150)
            grid_x, grid_y = np.meshgrid(grid_lon, grid_lat)

            # RBF interpolation on the specific metric field
            rbf = Rbf(df['lon'], df['lat'], df[field], function='linear')
            z_interp = rbf(grid_x, grid_y)

            # Mask outside convex hull
            mask = np.zeros_like(grid_x, dtype=bool)
            for i in range(grid_x.shape[0]):
                for j in range(grid_x.shape[1]):
                    if not hull_poly_simple.contains(Point(grid_x[i, j], grid_y[i, j])):
                        mask[i, j] = True

            z_interp[mask] = np.nan

            """ Generate result """

            levels = levels_map.get(field, [0, 50, 100, 150])
            colors = colors_map.get(field)

            geojson = createGeojson(grid_x, grid_y, z_interp, levels, hull_poly_simple, colors)

            """ Save Result """
            filename = f"contours_{field}.geojson"
            with open(filename, 'w') as f:
                json.dump(geojson, f, indent=2)
            print(f"Successfully generated {filename}")

            print(f"Stations included: {len(points)}")
            print(f"Contour levels used: {levels}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error loading metrics:", e)


if __name__ == "__main__":
    main()