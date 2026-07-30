from pywaterinfo import Waterinfo
import pandas as pd
from datetime import datetime, timezone
hic = Waterinfo("hic", cache=True)
vmm = Waterinfo("vmm", cache=True)


def fetch_stations(station_no,parameter_name="placeholder"):
    
    frames = []
    print("Station fetching started.")
    for station in station_no:
        station_data_hic = hic.get_timeseries_list(station_no=station)
        station_data_vmm = vmm.get_timeseries_list(station_no=station)
        frames.append(pd.DataFrame(station_data_hic))
        frames.append(pd.DataFrame(station_data_vmm))
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(f"../data/{parameter_name}_stations.csv", index=False)
    print("Station fetching finished & file saved.")

def fetch_timeseries(START_DATE, END_DATE,timeseriesgroup_ids,parameter_name="placeholder"):
    #timeseriesgroup_ids = ["289435042", "289423042", "289429042", "289441042"]
    frames = []
    print("Timeseries fetching started.")
    for group_id in timeseriesgroup_ids:
        
        try: 
            group_id_data = vmm.get_timeseries_values(group_id, start=START_DATE, end=END_DATE)
            frames.append(pd.DataFrame(group_id_data))
        except Exception as e:
            print(f"Error fetching data for group ID {group_id}: {e}")
        
        try: 
            group_id_data = hic.get_timeseries_values(group_id, start=START_DATE, end=END_DATE)
            frames.append(pd.DataFrame(group_id_data))
        except Exception as e:
            print(f"Error fetching data for group ID {group_id}: {e}")
            
        #frames.append(pd.DataFrame(group_id_data))
        
    df = pd.concat(frames, ignore_index=True)
    df.to_csv(f"../data/{parameter_name}.csv", index=False)
    print(f"{parameter_name} Timeseries fetching finished & file saved.")
    
def main():
    START_DATE = "2021-01-01T00:00:00Z"
    END_DATE = "2026-03-31T23:59:59Z"
    current_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    #fetch_stations(constants.waterlevel_stations, "waterlevel")
    fetch_timeseries(START_DATE, current_datetime,constants.waterlevel_sensors, "waterlevel")

if __name__ == "__main__":
    main()
