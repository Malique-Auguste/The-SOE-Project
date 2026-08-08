import pandas as pd
import numpy as np
from geopy.distance import geodesic
from datetime import datetime
from collections import deque

from shapely.geometry import Point, box
from pyproj import Geod

INCR = 0.03

print("loading crime db")
crime_db = pd.read_csv("data/crime_reports_2025_date.csv", parse_dates=["Date"])
print("loading do db")
do_db = pd.read_csv("data/d_o_database_coor_date.csv", parse_dates=["order_date"])
print("loading grid db")
grid_db = pd.read_csv(f"data/grid_{INCR:.2F}.csv")

#filter only murderous crimes, and data with coordinates
crime_db = crime_db[crime_db["primaryCrimeType"].isin(["Murder", "Attempted Murder", "Shooting", "Armed Robbery", "Home Invasion", "Carjacking", "Extortion", "Kidnapping"])]
crime_db = crime_db[pd.to_numeric(crime_db['Latitude'], errors='coerce').notnull()]
crime_db = crime_db[pd.to_numeric(crime_db['Latitude'], errors='coerce').notna()]
crime_db = crime_db.rename(columns={"Latitude": "lat", "Longitude": "long"})
do_db = do_db[pd.to_numeric(do_db['lat'], errors='coerce').notnull()]
do_db = do_db[pd.to_numeric(do_db['lat'], errors='coerce').notna()]

#filter database for only 2025
start_date = datetime(2025,1,1)
end_date = datetime(2025,12,31)
crime_db = crime_db[crime_db["Date"].between(start_date, end_date)]
do_db = do_db[do_db["order_date"].between(start_date, end_date)]

#change dates to week num from 1st of Jan, 2025
crime_db["week_num"] = np.floor((crime_db["Date"] - start_date) / pd.Timedelta(weeks=1)).astype(int)
do_db["week_num"] = np.floor((do_db["order_date"] - start_date) / pd.Timedelta(weeks=1)).astype(int)

#Counts the number of rows with coordinates within a box during a specific week
def count_by_week(bbox: Point, week_num, db):
    coors = db[db["week_num"] == week_num][["lat", "long"]]
    count = 0
    for coor in coors.itertuples():
        if bbox.contains(Point(coor.long, coor.lat)):
            count += 1

    return count

#Counts the number of rows outside of the bounding box but within a circle twice the radius of the circle that would be inscribed in the box
geod = Geod(ellps="WGS84")
def spillover_by_week(bbox: box, week_num, db):
    minx, _, _, _ = bbox.bounds
    radius = geod.line_length([bbox.centroid.x, minx], [bbox.centroid.y, bbox.centroid.y]) / 1000

    coors = db[db["week_num"] == week_num][["lat", "long"]]
    spillover = 0

    for coor in coors.itertuples():
        if not bbox.contains(Point(coor.long, coor.lat)):
            distance = geod.line_length([bbox.centroid.x, float(coor.long)], [bbox.centroid.y, float(coor.lat)]) / 1000
            if radius < distance <= 2*radius:
                spillover += 1 / (distance + 0.5)
    
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
    counts = deque([None, None, None, None, None, None, None, None])
    spillovers = deque([None, None, None, None, None, None, None, None])

    #iterates through each year
    for i in range(0, 53):
        counts.appendleft(count_by_week(bbox, i, do_db))
        spillovers.appendleft(spillover_by_week(bbox, i, do_db))

        crime_num = count_by_week(bbox, i, crime_db)
        row = pd.Series({
            "grid_id": grid_block.grid_id,
            "lat": grid_block.lat,
            "long": grid_block.long,
            "week_num": i,
            "crime_num": crime_num,
            "do_num": counts[0],
            "do_num_1": counts[1],
            "do_num_2": counts[2],
            "do_num_3": counts[3],
            "do_num_4": counts[4],
            "do_num_5": counts[5],
            "do_num_6": counts[6],
            "do_num_7": counts[7],
            "do_spill": spillovers[0],
            "do_spill_1": spillovers[1],
            "do_spill_2": spillovers[2],
            "do_spill_3": spillovers[3],
            "do_spill_4": spillovers[4],
            "do_spill_5": spillovers[5],
            "do_spill_6": spillovers[6],
            "do_spill_7": spillovers[7],
        }).to_frame().T

        counts.pop()
        spillovers.pop()

        aggr_db = pd.concat([aggr_db, row])

aggr_db.to_csv(f"data/aggr_{INCR:.2f}_db.csv", index=False)
print(aggr_db.describe())