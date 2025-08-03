

import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon
from shapely.errors import TopologicalError
import matplotlib.colors as mcolors
import matplotlib.cm as cm


def createGeojson(grid_x, grid_y, z_data, levels, hull_poly):
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
            rgba = sm.to_rgba(level)  # Get RGBA color for this level
            hex_color = mcolors.rgb2hex(rgba)  # Convert to HEX
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
                            "max_temp": float(level + (levels[1]-levels[0])/2),
                            "color": hex_color,  # HEX color
                            "fill": hex_color,   # For web maps
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
