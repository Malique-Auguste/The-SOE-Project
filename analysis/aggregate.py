import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
from collections import deque

from shapely.geometry import Point, box
from pyproj import Geod

#Geogrphic subdivision
#0.03 = 1st, 0.05 = 2nd, 0.1 = 3rd
ALPHA = 0.03
#Temporal unit of analysis
#4 days = 1st, 7 days = 2nd
LAMBDA = 4
START_DATE = datetime(2025,1,1)
END_DATE = datetime(2025,12,31)

PRECISION = True

print(f"Alpha {ALPHA}, Lambda {LAMBDA}, Precision {PRECISION}, Start Date {START_DATE}, End Date {END_DATE}")

print("loading crime db")
crime_db = pd.read_csv("data/crime_reports_2025_date.csv", parse_dates=["Date"])
print("loading do db")
do_db = pd.read_csv("data/d_o_database_coor_date.csv", parse_dates=["order_date"])
print("loading grid db")
grid_db = pd.read_csv(f"data/grid_{ALPHA:.2F}.csv")

#Renaming and formatting databases
crime_db = crime_db[pd.to_numeric(crime_db['Latitude'], errors='coerce').notnull()]
crime_db = crime_db[pd.to_numeric(crime_db['Latitude'], errors='coerce').notna()]
crime_db = crime_db.rename(columns={"Latitude": "lat", "Longitude": "long"})
do_db = do_db[pd.to_numeric(do_db['lat'], errors='coerce').notnull()]
do_db = do_db[pd.to_numeric(do_db['lat'], errors='coerce').notna()]

#Filter vioent crimes
if PRECISION == True:
    crime_db = crime_db[crime_db["primaryCrimeType"].isin(["Murder", "Attempted Murder", "Shooting", "Armed Robbery"])]
else:
    crime_db = crime_db[crime_db["primaryCrimeType"].isin(["Murder", "Attempted Murder", "Shooting", "Armed Robbery", "Home Invasion", "Carjacking", "Extortion", "Kidnapping"])]
    
#Filter for only 2025
crime_db = crime_db[crime_db["Date"].between(START_DATE, END_DATE)]
do_db = do_db[do_db["order_date"].between(START_DATE, END_DATE)]

#Change dates to numbered temporal units from 1st of Jan, 2025
crime_db["lambda_num"] = np.floor((crime_db["Date"] - START_DATE) / pd.Timedelta(days=LAMBDA)).astype(int)
do_db["lambda_num"] = np.floor((do_db["order_date"] - START_DATE) / pd.Timedelta(days=LAMBDA)).astype(int)

num_periods = max(crime_db["lambda_num"].max(), do_db["lambda_num"].max())
NUM_LEADS = 2


#Counts the number of rows with coordinates within a box during a specific week
def count_by_period(bbox: Point, lambda_num, db):
    coors = db[db["lambda_num"] == lambda_num][["lat", "long"]]
    count = 0
    for coor in coors.itertuples():
        if bbox.contains(Point(coor.long, coor.lat)):
            count += 1

    return count

#Counts the number of rows outside of the bounding box but within a circle twice the radius of the circle that would be inscribed in the box
geod = Geod(ellps="WGS84")
def spillover_by_period(bbox: box, lambda_num, db):
    minx, miny, _, _ = bbox.bounds
    neighbour_bbox = box(bbox.centroid.x - 3 * (bbox.centroid.x - minx),
                         bbox.centroid.y - 3 * (bbox.centroid.y - miny),
                         bbox.centroid.x + 3 * (bbox.centroid.x - minx),
                         bbox.centroid.y + 3 * (bbox.centroid.y - miny))
    
    coors = db[db["lambda_num"] == lambda_num][["lat", "long"]]
    spillover = 0

    for coor in coors.itertuples():
        coor = Point(coor.long, coor.lat)
        if neighbour_bbox.contains(coor) and (not bbox.contains(coor)):
            distance = geod.line_length([bbox.centroid.x, float(coor.x)], [bbox.centroid.y, float(coor.y)]) / 1000
            spillover += 1 / (distance + 0.1)
    
    return spillover

aggr_db = pd.DataFrame()

#iterates through and aggregates for each grid box
for grid_block in grid_db.itertuples():
    if "3" in grid_block.grid_id:
        print(grid_block.grid_id)

    bbox = box(grid_block.long - grid_block.incr / 2, 
               grid_block.lat - grid_block.incr / 2,
               grid_block.long + grid_block.incr / 2,
               grid_block.lat + grid_block.incr / 2)

    #stores the crime counts and spillover in deques so that values for the current week are appended to the front
    #  and deleted from the back when they become irrelevant
    counts = deque([None, None, None, None, None, None, None, None, None, None, None])
    spillovers = deque([None, None, None, None, None, None, None, None, None, None, None])

    #iterates through each period
    for i in range(0, num_periods + NUM_LEADS + 1):
        counts.appendleft(count_by_period(bbox, i, do_db))
        spillovers.appendleft(spillover_by_period(bbox, i, do_db))

        if i < NUM_LEADS:
            continue
        elif i > num_periods:
            counts[0] = None
            spillovers[0] = None


        lambda_num = i - NUM_LEADS

        crime_num = count_by_period(bbox, lambda_num, crime_db)
        row = pd.Series({
            "grid_id": grid_block.grid_id,
            "lat": grid_block.lat,
            "long": grid_block.long,
            "lambda_num": lambda_num,
            "crime_num": crime_num,
            "x2": counts[0],
            "x1": counts[1],
            "x0": counts[2],
            "x_1": counts[3],
            "x_2": counts[4],
            "x_3": counts[5],
            "x_4": counts[6],
            "x_5": counts[7],
            "x_6": counts[8],
            "x_7": counts[9],
            "x_8": counts[10],
            "x2_d": counts[0] - counts[1],
            "x1_d": counts[1] - counts[2],
            "x0_d": counts[2] - counts[3],
            "x_1_d": counts[3] - counts[4],
            "x_2_d": counts[4] - counts[5],
            "x_3_d": counts[5] - counts[6],
            "x_4_d": counts[6] - counts[7],
            "x_5_d": counts[7] - counts[8],
            "x_5_d": counts[8] - counts[9],
            "x_7_d": counts[9] - counts[10],       
            "s2": spillovers[0],
            "s1": spillovers[1],
            "s0": spillovers[2],
            "s_1": spillovers[3],
            "s_2": spillovers[4],
            "s_3": spillovers[5],
            "s_4": spillovers[6],
            "s_5": spillovers[7],
            "s_6": spillovers[8],
            "s_7": spillovers[9],
            "s_8": spillovers[10],
            "s2_d": spillovers[0] - spillovers[1],
            "s1_d": spillovers[1] - spillovers[2],
            "s0_d": spillovers[2] - spillovers[3],
            "s_1_d": spillovers[3] - spillovers[4],
            "s_2_d": spillovers[4] - spillovers[5],
            "s_3_d": spillovers[5] - spillovers[6],
            "s_4_d": spillovers[6] - spillovers[7],
            "s_5_d": spillovers[7] - spillovers[8],
            "s_5_d": spillovers[8] - spillovers[9],
            "s_7_d": spillovers[9] - spillovers[10]
        }).to_frame().T

        counts.pop()
        spillovers.pop()

        aggr_db = pd.concat([aggr_db, row])

aggr_db.to_csv(f"data/aggr_{ALPHA:.2f}_{LAMBDA:.0F}_{PRECISION}_db.csv", index=False)
print(aggr_db.describe())

print(f"Alpha {ALPHA}, Lambda {LAMBDA}, Precision {PRECISION}, Start Date {START_DATE}, End Date {END_DATE}")
