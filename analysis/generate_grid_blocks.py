import geopandas as gpd
import pandas as pd
from shapely.geometry import Point, shape, box

#Loads boundary map of TnT
country_geom = gpd.read_file("data/tto_adm0/TTO_adm0.shp")
print("Loaded country geom")

#Max and min corners for a bounding box for TnT
bottom_corner = Point(-61.9, 10.0)
top_corner = Point(-60.5, 11.4)

#Generates empty db to store grids
db = pd.DataFrame(columns=["lat", "long", "grid_id", "incr"])

#Signifies the width and height of the grid cells in lat and long degrees
#If increment is 0.1, then the grid cell is 0.1 of a long and lat deg in width and height
increment = 0.03

#Breaks the bounding box for TnT into smaller grid cells based on incremenet and iterates through it
#Deletes grid cells that do not overlap with TnT land (omit ocean only grid cells)
for i in range(1, int((top_corner.x - bottom_corner.x) / increment) + 2):
    for j in range(1, int((top_corner.y - bottom_corner.y) / increment) + 2):

        min_x = bottom_corner.x + (i-1)*increment
        min_y = bottom_corner.y + (j-1)*increment
        max_x = bottom_corner.x + (i)*increment
        max_y = bottom_corner.y + (j)*increment

        grid_block = box(min_x, min_y, max_x, max_y)

        #saves gridcell by midpoint if it intersects with trinidad ro tobago land
        if country_geom.intersects(grid_block).item():
            row = pd.Series({"lat": grid_block.centroid.y, "long":grid_block.centroid.x, "grid_id": f"{i}_{j}", "incr": increment}).to_frame().T
            db = pd.concat([db, row])

            #saves the database with every addition of 200 rows
            if len(db) % 200 == 0:
                print(row)
                db.to_csv(f"data/grid_{increment:.2f}.csv", index = False)

#saves the database by increment size
db.to_csv(f"data/grid_{increment:.2f}.csv", index = False)
