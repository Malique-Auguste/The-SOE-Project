#gemini optimised version of my script. Compared outputs with test files between this and the og script to ensure consistency

import pandas as pd
import numpy as np
import geopandas as gpd
from shapely.geometry import box
from pyproj import Geod
from datetime import datetime

# Geographic subdivision
al = [0.03, 0.05, 0.1]
#temporal variaiton
la = [4, 7]
#violent crime precision
pr = [True, False]

START_DATE = datetime(2025, 1, 1)
END_DATE = datetime(2025, 12, 31)


for ALPHA in al:
    for LAMBDA in la:
        for PRECISION in pr:
            print(f"Alpha {ALPHA}, Lambda {LAMBDA}, Precision {PRECISION}, Start Date {START_DATE}, End Date {END_DATE}")

            # Load databases
            print("loading crime db")
            crime_db = pd.read_csv("data/crime_reports_2025_date.csv", parse_dates=["Date"])
            print("loading do db")
            do_db = pd.read_csv("data/d_o_database_coor_date.csv", parse_dates=["order_date"])
            print("loading grid db")
            grid_db = pd.read_csv(f"data/grid_{ALPHA:.2f}.csv")

            # Clean numeric coordinates
            crime_db['Latitude'] = pd.to_numeric(crime_db['Latitude'], errors='coerce')
            crime_db['Longitude'] = pd.to_numeric(crime_db['Longitude'], errors='coerce')
            crime_db = crime_db.dropna(subset=['Latitude', 'Longitude']).rename(columns={"Latitude": "lat", "Longitude": "long"})

            do_db['lat'] = pd.to_numeric(do_db['lat'], errors='coerce')
            do_db['long'] = pd.to_numeric(do_db['long'], errors='coerce')
            do_db = do_db.dropna(subset=['lat', 'long'])

            # Filter crime types
            crime_types = ["Murder", "Attempted Murder", "Shooting", "Armed Robbery"]
            if not PRECISION:
                crime_types.extend(["Home Invasion", "Carjacking", "Extortion", "Kidnapping"])

            crime_db = crime_db[crime_db["primaryCrimeType"].isin(crime_types)]

            # Filter date ranges
            crime_db = crime_db[crime_db["Date"].between(START_DATE, END_DATE)]
            do_db = do_db[do_db["order_date"].between(START_DATE, END_DATE)]

            # Compute temporal units
            crime_db["lambda_num"] = np.floor((crime_db["Date"] - START_DATE) / pd.Timedelta(days=LAMBDA)).astype(int)
            do_db["lambda_num"] = np.floor((do_db["order_date"] - START_DATE) / pd.Timedelta(days=LAMBDA)).astype(int)

            num_periods = max(crime_db["lambda_num"].max(), do_db["lambda_num"].max())

            # --- VECTORIZED GEOSPATIAL PREPARATION ---

            # Create GeoDataFrames
            crime_gdf = gpd.GeoDataFrame(
                crime_db.reset_index(drop=True), 
                geometry=gpd.points_from_xy(crime_db['long'], crime_db['lat']), 
                crs="EPSG:4326"
            )

            do_gdf = gpd.GeoDataFrame(
                do_db.reset_index(drop=True), 
                geometry=gpd.points_from_xy(do_db['long'], do_db['lat']), 
                crs="EPSG:4326"
            )

            # Build inner bounding boxes and neighbor bounding boxes
            half_incr = grid_db['incr'] / 2.0
            inner_boxes = [
                box(long - inc, lat - inc, long + inc, lat + inc)
                for long, lat, inc in zip(grid_db['long'], grid_db['lat'], half_incr)
            ]
            neighbor_boxes = [
                box(long - 3 * inc, lat - 3 * inc, long + 3 * inc, lat + 3 * inc)
                for long, lat, inc in zip(grid_db['long'], grid_db['lat'], half_incr)
            ]

            grid_inner_gdf = gpd.GeoDataFrame(grid_db[['grid_id', 'lat', 'long']], geometry=inner_boxes, crs="EPSG:4326")
            grid_neighbor_gdf = gpd.GeoDataFrame(
                grid_db[['grid_id', 'lat', 'long']].rename(
                    columns={'grid_id': 'neighbor_grid_id', 'lat': 'neighbor_lat', 'long': 'neighbor_long'}
                ), 
                geometry=neighbor_boxes, 
                crs="EPSG:4326"
            )

            # 1. Inner Box Crime Counts
            crime_joined = gpd.sjoin(crime_gdf, grid_inner_gdf, predicate='within')
            crime_counts = crime_joined.groupby(['grid_id', 'lambda_num']).size().reset_index(name='y')

            # 2. Inner Box DO Counts
            do_joined_inner = gpd.sjoin(do_gdf, grid_inner_gdf, predicate='within')
            do_counts = do_joined_inner.groupby(['grid_id', 'lambda_num']).size().reset_index(name='do_count')

            # 3. Spillover Calculation
            do_joined_neighbor = gpd.sjoin(do_gdf, grid_neighbor_gdf, predicate='within')

            # Map each point to its inner grid cell to filter points inside target box
            point_inner_map = do_joined_inner.groupby(level=0)['grid_id'].first().to_frame('inner_grid_id')
            do_joined_neighbor = do_joined_neighbor.join(point_inner_map)

            spillover_candidates = do_joined_neighbor[
                do_joined_neighbor['inner_grid_id'] != do_joined_neighbor['neighbor_grid_id']
            ].copy()

            # Vectorized PyProj distance calculation
            geod = Geod(ellps="WGS84")
            _, _, dist_meters = geod.inv(
                spillover_candidates['long'].values,
                spillover_candidates['lat'].values,
                spillover_candidates['neighbor_long'].values,
                spillover_candidates['neighbor_lat'].values
            )

            spillover_candidates['spillover_val'] = 1.0 / ((dist_meters / 1000.0) + 0.1)

            spillover_counts = (
                spillover_candidates.groupby(['neighbor_grid_id', 'lambda_num'])['spillover_val']
                .sum()
                .reset_index()
                .rename(columns={'neighbor_grid_id': 'grid_id', 'spillover_val': 'spillover'})
            )

            # --- TIME SERIES LAG/LEAD FEATURE MATRIX ---

            # Create full Cartesian product of (grid_id, lambda_num)
            grid_ids = grid_db['grid_id'].unique()
            periods = np.arange(0, num_periods + 1)
            full_grid = pd.MultiIndex.from_product([grid_ids, periods], names=['grid_id', 'lambda_num']).to_frame().reset_index(drop=True)

            # Merge grid centroids and aggregated counts
            full_grid = full_grid.merge(grid_db[['grid_id', 'lat', 'long']], on='grid_id', how='left')
            full_grid = full_grid.merge(crime_counts, on=['grid_id', 'lambda_num'], how='left')
            full_grid = full_grid.merge(do_counts, on=['grid_id', 'lambda_num'], how='left')
            full_grid = full_grid.merge(spillover_counts, on=['grid_id', 'lambda_num'], how='left')

            full_grid[['y', 'do_count', 'spillover']] = full_grid[['y', 'do_count', 'spillover']].fillna(0)
            full_grid = full_grid.sort_values(['grid_id', 'lambda_num']).reset_index(drop=True)

            # Generate Lag/Lead features
            grouped = full_grid.groupby('grid_id')

            x_cols = ['x2', 'x1', 'x0', 'x_1', 'x_2', 'x_3', 'x_4', 'x_5', 'x_6', 'x_7', 'x_8']
            s_cols = ['s2', 's1', 's0', 's_1', 's_2', 's_3', 's_4', 's_5', 's_6', 's_7', 's_8']
            shifts = [-2, -1, 0, 1, 2, 3, 4, 5, 6, 7, 8]

            for x_name, s_name, shift_val in zip(x_cols, s_cols, shifts):
                full_grid[x_name] = grouped['do_count'].shift(shift_val)
                full_grid[s_name] = grouped['spillover'].shift(shift_val)

            # Compute Differences
            for i in range(len(x_cols) - 1):
                full_grid[f"{x_cols[i]}_d"] = full_grid[x_cols[i]] - full_grid[x_cols[i+1]]
                full_grid[f"{s_cols[i]}_d"] = full_grid[s_cols[i]] - full_grid[s_cols[i+1]]

            # Assemble final schema
            final_cols = ['grid_id', 'lat', 'long', 'lambda_num', 'y'] + \
                        x_cols + [f"{col}_d" for col in x_cols[:-1]] + \
                        s_cols + [f"{col}_d" for col in s_cols[:-1]]

            aggr_db = full_grid[final_cols]

            db = aggr_db.sort_values(by=["grid_id", "lambda_num"])
            
            # 2. Compute lags grouped by entity
            # Compute y_1 through y_8 in a single pass
            num_y_lags = 8
            grouped_y = aggr_db.groupby("grid_id")["y"]

            y_lag_dict = {
                f"y_{k}": grouped_y.shift(k) 
                for k in range(1, num_y_lags + 1)
            }

            # Assign all new columns in one unified call
            aggr_db = aggr_db.assign(**y_lag_dict)

            aggr_db.to_csv(f"data/aggr_{ALPHA:.2f}_{LAMBDA:.0f}_{PRECISION}_db.csv", index=False)
            print(aggr_db.describe())
            print(f"Alpha {ALPHA}, Lambda {LAMBDA}, Precision {PRECISION}, Start Date {START_DATE}, End Date {END_DATE}")