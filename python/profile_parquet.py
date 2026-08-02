import pandas as pd

file_path = "../data_in/yellow_tripdata_2024-01.parquet"

df = pd.read_parquet(file_path)

print(df.head(10))

print(df.shape)
print(df.columns.tolist())
print(df.dtypes)

print(df["fare_amount"].head(10))
print(type(df["fare_amount"].iloc[0]))