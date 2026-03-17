from pywaterinfo import Waterinfo
import pandas as pd
hic = Waterinfo("hic", cache=True)
vmm = Waterinfo("vmm", cache=True)

def fetch_stations():
    station_no = ["HIS_BWO_VITO_IOW50","HIS_BWO_VITO_IOW48","BWO_VITO_IOW49","BWO_VITO_IOW51"]
    df = pd.DataFrame()
    for station in station_no:
        station = vmm.get_timeseries_list(station_no=station)
        temp_df = pd.DataFrame(station)
        df = pd.concat([df, temp_df], ignore_index=True)
    df.to_csv("./data/stations.csv", index=False)

def main():
    fetch_stations()

if __name__ == "__main__":
    main()