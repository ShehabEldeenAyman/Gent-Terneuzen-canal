import pandas as pd
import sys; sys.path.append('..')  # Adds the parent directory


def fetch_water_link_data(START_DATE,END_DATE):
    df = pd.read_csv("../data/water-link/data.xlsx")

    #Incomplete / Unnecessary