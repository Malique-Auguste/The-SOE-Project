from datetime import datetime
import dateutil
import pandas as pd

from dateutil import parser

#Converts the date formats of the preventative detention orders and crime databases to a consistent format 

do_db = pd.read_csv("data/d_o_database_coor.csv")
original_date = do_db["order_date"].str.replace(r'(\d+)(st|nd|rd|th) day ', r'\1 ', regex=True)
formatted_date = pd.to_datetime(original_date, format="%d  of %B, %Y", errors="coerce")
do_db["order_date"] = formatted_date
do_db.to_csv("data/d_o_database_coor_date.csv", index=False)

crime_db = pd.read_csv("data/crime_reports_2025.csv")
crime_db["Date"] = crime_db["Date"].str.strip()
crime_db["Date"] = pd.to_datetime(crime_db["Date"], format = "%m/%d/%Y")
crime_db.to_csv("data/crime_reports_2025_date.csv", index=False)