import pandas as pd
from datetime import datetime

def preprocess(parameter_name="placeholder"):
    # If your file is actually an Excel file (.xlsx), change this to pd.read_excel
    df = pd.read_csv(f'../data/{parameter_name}.csv')
    
    # 1. Convert the 'Timestamp' column to datetime objects
    df['Timestamp'] = pd.to_datetime(df['Timestamp'])
    
    # 2. Format the datetime to the desired ISO 8601 structure (e.g., 2025-02-22T04:15:00Z)
    # %Y-%m-%dT%H:%M:%SZ explicitly defines the format you want
    df['Timestamp'] = df['Timestamp'].dt.strftime('%Y-%m-%dT%H:%M:%SZ')
    
    print(df.head())
    
    # Save the modified dataframe back
    df.to_csv(f'../data/{parameter_name}.csv', index=False)


def main():
    preprocess()

if __name__ == "__main__":
    main()