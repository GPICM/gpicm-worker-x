from dotenv import load_dotenv

print("Loading environment variables")
load_dotenv()

import json
import numpy as np
import pandas as pd

from scipy.interpolate import Rbf
from shapely.geometry import Point, shape
from data.load_metrics import loadMetrics
from data.create_geojson import createGeojson


def main():


    try:
        print("Loading Default GeoJson borders")
        with open("./monitoring-map/macae.json") as f:
            border_geojson = json.load(f)

        # Extrair a geometria (Polygon ou MultiPolygon)
        hull_poly = shape(border_geojson["features"][0]["geometry"])

        print("Loading Metrics")
        metrics = loadMetrics()
        # Transformar a lista de dicts em DataFrame
        df = pd.DataFrame(metrics)
        
        # Agora pegar os pontos como numpy array
        points = df[['lon', 'lat']].values

        # Interpolation grid
        buffer = 0.05
        grid_lon = np.linspace(df['lon'].min() - buffer, df['lon'].max() + buffer, 150)
        grid_lat = np.linspace(df['lat'].min() - buffer, df['lat'].max() + buffer, 150)
        grid_x, grid_y = np.meshgrid(grid_lon, grid_lat)

        # RBF interpolation
        rbf = Rbf(df['lon'], df['lat'], df['value'], function='linear')
        z_interp = rbf(grid_x, grid_y)

        # Mask outside convex hull
        mask = np.zeros_like(grid_x, dtype=bool)
        for i in range(grid_x.shape[0]):
            for j in range(grid_x.shape[1]):
                if not hull_poly.contains(Point(grid_x[i, j], grid_y[i, j])):
                    mask[i, j] = True

        z_interp[mask] = np.nan
        # k= 0.5
        z_round = z_interp  # np.round(0.5 * z_interp) / 0.5  # Optional rounding

        
        """ z_min = np.nanmin(z_interp)
        z_max = np.nanmax(z_interp)
        print(f"z_min: {z_min}, z_max: {z_max}")
        z_round = np.clip(z_round, z_min, z_max) """

        # Generate levels and GeoJSON
        levels = np.arange(np.nanmin(z_round), np.nanmax(z_round) + 0.5, 0.5)
        geojson = createGeojson(grid_x, grid_y, z_round, levels, hull_poly)

        with open('contours.geojson', 'w') as f:
            json.dump(geojson, f, indent=2)

        print("Successfully generated contours GeoJSON!")
        print(f"Stations included: {len(points)}")
        print(f"Contour levels used: {levels}")

    except Exception as e:
        import traceback
        traceback.print_exc()
        print("Error loading metrics:", e)


if __name__ == "__main__":
    main()
