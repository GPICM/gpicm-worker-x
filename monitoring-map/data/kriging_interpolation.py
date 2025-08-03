from pykrige.ok import OrdinaryKriging

def kriging_interpolation(df, field, grid_lon, grid_lat):
    """Aplica Kriging aos dados de entrada e retorna a grade interpolada"""

    print(f"Interpolando com Kriging para o campo {field}")

    try:
        OK = OrdinaryKriging(
            df['lon'], 
            df['lat'], 
            df[field], 
            variogram_model='linear',  # você pode testar também 'spherical', 'exponential', etc.
            verbose=False, enable_plotting=False
        )

        # A grade precisa estar 1D para o Kriging
        z_interp, ss = OK.execute('grid', grid_lon, grid_lat)
        return z_interp

    except Exception as e:
        print(f"Erro ao interpolar com Kriging para {field}: {e}")
        return None
