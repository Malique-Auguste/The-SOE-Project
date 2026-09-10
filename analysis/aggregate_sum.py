import pandas as pd
import numpy as np

#Geogrphic subdivision
#0.03 = 1st, 0.05 = 2nd, 0.1 = 3rd
al = [0.03, 0.05, 0.1]
#Temporal unit of analysis
#4 days = 1st, 7 days = 2nd
la = [4,7]

pr = [True, False]


for ALPHA in al:
    for LAMBDA in la:
        for PRECISION in pr:
            aggr_db_name = f"aggr_{ALPHA:.2f}_{LAMBDA:.0F}_{PRECISION}_db"

            aggr_db = pd.read_csv(f"data/{aggr_db_name}.csv")
            aggr_db["do_num_1_s"] = aggr_db["do_num_1"] - aggr_db["do_num_2"]
            aggr_db["do_num_2_s"] = aggr_db["do_num_2"] - aggr_db["do_num_3"]
            aggr_db["do_num_3_s"] = aggr_db["do_num_3"] - aggr_db["do_num_4"]
            aggr_db["do_num_4_s"] = aggr_db["do_num_4"] - aggr_db["do_num_5"]
            aggr_db["do_num_5_s"] = aggr_db["do_num_5"] - aggr_db["do_num_6"]
            aggr_db["do_num_6_s"] = aggr_db["do_num_6"] - aggr_db["do_num_7"]
            aggr_db["do_num_7_s"] = aggr_db["do_num_7"] - aggr_db["do_num_8"]

            aggr_db["do_spill_1_s"] = aggr_db["do_spill_1"] - aggr_db["do_spill_2"]
            aggr_db["do_spill_2_s"] = aggr_db["do_spill_2"] - aggr_db["do_spill_3"]
            aggr_db["do_spill_3_s"] = aggr_db["do_spill_3"] - aggr_db["do_spill_4"]
            aggr_db["do_spill_4_s"] = aggr_db["do_spill_4"] - aggr_db["do_spill_5"]
            aggr_db["do_spill_5_s"] = aggr_db["do_spill_5"] - aggr_db["do_spill_6"]
            aggr_db["do_spill_6_s"] = aggr_db["do_spill_6"] - aggr_db["do_spill_7"]
            aggr_db["do_spill_7_s"] = aggr_db["do_spill_7"] - aggr_db["do_spill_8"]

            aggr_db.to_csv(f"data/{aggr_db_name}_s.csv")