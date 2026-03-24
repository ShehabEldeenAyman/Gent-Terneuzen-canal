from pywaterinfo import Waterinfo
import pandas as pd

hic = Waterinfo("hic", cache=True)
vmm = Waterinfo("vmm", cache=True)

def fetch_stations():
    station_no = ["HIS_BWO_VITO_IOW50", "HIS_BWO_VITO_IOW48", "BWO_VITO_IOW49", "BWO_VITO_IOW51"]
    frames = []
    print("Station fetching started.")
    for station in station_no:
        station_data = vmm.get_timeseries_list(station_no=station)
        frames.append(pd.DataFrame(station_data))
    df = pd.concat(frames, ignore_index=True)
    df.to_csv("./data/stations.csv", index=False)
    print("Station fetching finished & file saved.")

def fetch_timeseries():
    timeseriesgroup_ids = ["289435042", "289423042", "289429042", "289441042"]
    frames = []
    print("Timeseries fetching started.")
    for group_id in timeseriesgroup_ids:
        group_id_data = vmm.get_timeseries_values(
            group_id, start="2023-01-01T00:00:00Z", end="2025-12-31T23:59:59Z"
        )
        frames.append(pd.DataFrame(group_id_data))
    df = pd.concat(frames, ignore_index=True)
    df.to_csv("./data/timeseries.csv", index=False)
    print("Timeseries fetching finished & file saved.")

def main():
    fetch_stations()
    fetch_timeseries()

if __name__ == "__main__":
    main()