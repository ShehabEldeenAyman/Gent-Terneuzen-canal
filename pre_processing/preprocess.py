import pandas as pd
from datetime import datetime

def preprocess():
    df = pd.read_csv('../data/timeseries.csv')
    df['unixtimestamp'] = pd.to_datetime(df['Timestamp']).astype('int64') // 10**9
    print(df.head())
    df.to_csv('../data/timeseries.csv', index=False)


def main():
    preprocess()

if __name__ == "__main__":
    main()