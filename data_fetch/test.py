from pywaterinfo import Waterinfo
import pandas as pd
from datetime import datetime, timezone

hic = Waterinfo("hic", cache=True)
vmm = Waterinfo("vmm", cache=True)


def fetch_stations():
    station_no = ["325066"]
    frames = []
    print("Station fetching started.")
    for station in station_no:
        station_data = vmm.get_timeseries_list(station_no=station)
        frames.append(pd.DataFrame(station_data))
    df = pd.concat(frames, ignore_index=True)
    df.to_csv("stations.csv", index=False)
    print("Station fetching finished & file saved.")

def fetch_timeseries(START_DATE, END_DATE):
    timeseriesgroup_ids = ["34967042"]
    frames = []
    print("Timeseries fetching started.")
    for group_id in timeseriesgroup_ids:
        group_id_data = vmm.get_timeseries_values(
            group_id, start=START_DATE, end=END_DATE
        )
        frames.append(pd.DataFrame(group_id_data))
    df = pd.concat(frames, ignore_index=True)
    df.to_csv("timeseries.csv", index=False)
    print("Timeseries fetching finished & file saved.")
    return (END_DATE)

def main():
    START_DATE = "2021-01-01T00:00:00Z"
    END_DATE = "2026-03-24T23:59:59Z"
    current_datetime = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    #fetch_stations()
    fetch_timeseries(START_DATE, END_DATE)

if __name__ == "__main__":
    main()