

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.errors import TopologicalError
import matplotlib.colors as mcolors
import matplotlib.cm as cm


default_colors = [
    "#00A651",  # Normal (0 mm)
    "#0071BC",  # Observação (0.2–5 mm)
    "#FCEE21",  # Atenção (5.1–20 mm)
    "#F7931E",  # Alerta (20.1–40 mm)
    "#ED1C24",  # Alerta Máximo (40.1–50 mm)
    "#A50000",  # Extrema (>50 mm)
    "#410679",  # Extrema (>50 mm)
]

simplify_tolerance = 0.00025  # degrees (small for subtle simplification)

def createGeojson(grid_x, grid_y, z_data, levels, hull_poly, colors = default_colors):


    print("levels:",  len(levels))
    print("colors:",  len(colors))
    
    # Sanity check: must match number of color intervals
    if len(colors) < len(levels) - 1:
        print(f"Warning: colors count {len(colors)} is less than levels intervals {len(levels)-1} for field {field}")

    fig, ax = plt.subplots()
    cs = ax.contourf(grid_x, grid_y, z_data, levels=levels, cmap='turbo')
    features = []
    
    # --- Color Mapping Setup ---
    norm = mcolors.Normalize(vmin=min(levels), vmax=max(levels))
    cmap = cm.get_cmap('turbo')  # Must match the contourf cmap
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)

    # Safe way to access contour segments
    if hasattr(cs, 'allsegs'):
        for i in range(min(len(cs.levels), len(cs.allsegs))):  # Ensure we don't exceed bounds

        
            level = cs.levels[i]
            color = colors[i] 

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

                    clipped = clipped.simplify(simplify_tolerance, preserve_topology=True)
                     
                    if clipped.geom_type == 'Polygon':
                        coords = [np.array(clipped.exterior.coords).tolist()]
                    elif clipped.geom_type == 'MultiPolygon':
                        coords = [np.array(p.exterior.coords).tolist() for p in clipped.geoms]
                    else:
                        continue
                        
                    features.append({
                        "type": "Feature",
                        "properties": {
                            "value": float(level),
                            "min": float(level - (levels[1]-levels[0])/2),
                            "max": float(level + (levels[1]-levels[0])/2),
                            "color": color,  # HEX color
                            "fill": color,   # For web maps
                            "fill-opacity": 0.8  # Match your plot's alpha
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
            "description": "Value contours",
            "units": "m/s",
            "levels": [float(l) for l in levels],
        }
    }
