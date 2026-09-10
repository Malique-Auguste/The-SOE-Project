import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
from collections import deque

from shapely.geometry import Point, box
from pyproj import Geod

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
            db = pd.read_csv(f"data/aggr_{ALPHA:.2f}_{LAMBDA:.0f}_{PRECISION}_db.csv")

            # 1. Ensure data is correctly sorted
            db = db.sort_values(by=["grid_id", "lambda_num"])

            # 2. Compute lags grouped by entity
            db["y_lag1"] = db.groupby("grid_id")["crime_num_1"].shift(1)
            db["y_lag2"] = db.groupby("grid_id")["crime_num"].shift(2)

            print(db)
            quit()