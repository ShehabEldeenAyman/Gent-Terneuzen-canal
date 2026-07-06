import pandas as pd
from datetime import datetime

def preprocess(parameter_name="placeholder"):
    df = pd.read_csv(f'../data/{parameter_name}.csv')
    df['unixtimestamp'] = pd.to_datetime(df['Timestamp']).astype('int64') // 10**9
    print(df.head())
    df.to_csv(f'../data/{parameter_name}.csv', index=False)


def main():
    preprocess()

if __name__ == "__main__":
    main()