import detention_order_scraper as dos, detention_order_miner as dom
from debug_print import debug_print
import pandas as pd
import time, random


def run(years):
    database = pd.DataFrame()

    dos.change_session()

    for year in years:
        detention_order_download_links = dos.extract_pdf_download_links(year)

        for i in range(len(detention_order_download_links)):
            #As to not spam servers (DOS attack) and to avoide bot detectors we pause requests every 20 downloads.
            if i!=0 and i%20 == 0:
                dos.change_session()
                debug_print("Waiting 10s to cool down servers and temporarily save database", 1)
                database.to_csv("data/d_o_database_temp_20.csv", index = False)
                time.sleep(10)
                debug_print("  └── Completed waiting.", 1)
            
            #Downloades and mines data
            (id, link) = detention_order_download_links[i]
            dos.download_pdf_temp(id, link)
            mined_data = pd.DataFrame([dom.parse_detention_order(id)])
            database = pd.concat([database, mined_data])

            #As to not spam servers (DOS attack) and to avoide bot detectors pause requests for roughly ~0.5s.
            delay = random.uniform(0,1)
            debug_print(f"Waiting {delay:.1}s to cool down servers", 3)
            time.sleep(delay)
            debug_print("  └── Completed waiting.", 3)

        database.to_csv("data/d_o_database_temp_yearly.csv")
    
    database.to_csv("data/d_o_database.csv", index=False)

    print("\nDone.")

run(years = [2025, 2026])