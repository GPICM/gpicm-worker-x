
import json
import numpy as np
import pandas as pd

from scipy.interpolate import Rbf
from shapely.geometry import Point, shape
from data.load_metrics import loadMetrics
from data.create_geojson import createGeojson

def main():

    try:
        """ Baixar Limites """
    
        print("Loading Default GeoJson borders")
        with open("./monitoring-map/macae.json") as f:
            border_geojson = json.load(f)

        # Extrair a geometria (Polygon ou MultiPolygon)
        hull_poly = shape(border_geojson["features"][0]["geometry"])
        tolerance = 0.01  # degrees, adjust for desired simplification level
        hull_poly_simple = hull_poly.simplify(tolerance, preserve_topology=True)

        """ Carregar Metricas """

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

        print("zinterp", z_interp)


        """ Aplicando Mascaras """

        # Mask outside convex hull
        mask = np.zeros_like(grid_x, dtype=bool)
        for i in range(grid_x.shape[0]):
            for j in range(grid_x.shape[1]):
                if not hull_poly_simple.contains(Point(grid_x[i, j], grid_y[i, j])):
                    mask[i, j] = True

        z_interp[mask] = np.nan
        # k= 0.5
        z_round = z_interp  # np.round(0.5 * z_interp) / 0.5  # Optional rounding


        levels = [0.0, 45, 90, 125, 180, 240, 270]  # 6 intervals, 7 thresholds
        geojson = createGeojson(grid_x, grid_y, z_round, levels, hull_poly_simple)

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