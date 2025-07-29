from dotenv import load_dotenv

# Carrega variáveis do .env
load_dotenv()

from database import get_today_online_station_metrics

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from io import StringIO
import json
from shapely.geometry import Polygon, MultiPoint, Point
from scipy.interpolate import Rbf
from scipy.spatial import ConvexHull
from shapely.errors import TopologicalError

# Load and preprocess data

docs = list(get_today_online_station_metrics())


df = []

for i in range(0, 13):
    doc = docs[i]

    print(doc)

    dic = {
        "lon": doc.get("geoPosition").get("coordinates")[0],
        "lat": doc.get("geoPosition").get("coordinates")[1],
        "wind": doc.get("latestTemperature"),
        "station": doc.get("stationSlug")
    }
    df.append(dic)


# Transformar a lista de dicts em DataFrame
df = pd.DataFrame(df)

# Agora pegar os pontos como numpy array
points = df[['lon', 'lat']].values

hull = ConvexHull(points)
hull_poly = Polygon(points[hull.vertices])

# Interpolation grid
buffer = 0.05
grid_lon = np.linspace(df['lon'].min()-buffer, df['lon'].max()+buffer, 150)
grid_lat = np.linspace(df['lat'].min()-buffer, df['lat'].max()+buffer, 150)
grid_x, grid_y = np.meshgrid(grid_lon, grid_lat)

# RBF interpolation
rbf = Rbf(df['lon'], df['lat'], df['wind'], function='linear')
z_interp = rbf(grid_x, grid_y)

# Mask outside convex hull
mask = np.zeros_like(grid_x, dtype=bool)
for i in range(grid_x.shape[0]):
    for j in range(grid_x.shape[1]):
        if not hull_poly.contains(Point(grid_x[i,j], grid_y[i,j])):
            mask[i,j] = True

z_interp[mask] = np.nan
k= 0.5
z_round = z_interp#np.round(k * z_interp) / k  # Round to nearest 0.5

# Robust GeoJSON generation that handles edge cases
def create_geojson(grid_x, grid_y, z_data, levels):
    fig, ax = plt.subplots()
    cs = ax.contourf(grid_x, grid_y, z_data, levels=levels)
    
    features = []
    
    # Safe way to access contour segments
    if hasattr(cs, 'allsegs'):
        for i in range(min(len(cs.levels), len(cs.allsegs))):  # Ensure we don't exceed bounds
            level = cs.levels[i]
            for seg in cs.allsegs[i]:
                if len(seg) < 3:  # Need at least 3 points
                    continue
                    
                # Close the polygon
                closed_seg = np.vstack([seg, seg[0]])
                try:
                    poly = Polygon(closed_seg)
                    if not poly.is_valid:
                        poly = poly.buffer(0)
                    
                    clipped = poly.intersection(hull_poly)
                    if clipped.is_empty:
                        continue
                        
                    if clipped.geom_type == 'Polygon':
                        coords = [np.array(clipped.exterior.coords).tolist()]
                    elif clipped.geom_type == 'MultiPolygon':
                        coords = [np.array(p.exterior.coords).tolist() for p in clipped.geoms]
                    else:
                        continue
                        
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "temperature": float(level),
                            "min_temp": float(level - (levels[1]-levels[0])/2),
                            "max_temp": float(level + (levels[1]-levels[0])/2)
                        },
                        "geometry": {
                            "type": "Polygon" if clipped.geom_type == 'Polygon' else "MultiPolygon",
                            "coordinates": coords
                        }
                    })
                except (ValueError, TopologicalError):
                    continue
    
    plt.close(fig)
    return {
        "type": "FeatureCollection",
        "features": features,
        "properties": {
            "description": "Wind gust contours",
            "units": "m/s",
            "levels": [float(l) for l in levels],
            "station_count": len(points)
        }
    }

# Generate levels and GeoJSON
levels = np.arange(np.nanmin(z_round), np.nanmax(z_round) + 0.5, 0.5)
geojson = create_geojson(grid_x, grid_y, z_round, levels)

# Save output
with open('wind_gust_contours.geojson', 'w') as f:
    json.dump(geojson, f, indent=2)

print("Successfully generated wind gust contours GeoJSON!")
print(f"Contour levels used: {levels}")
print(f"Stations included: {len(points)}")