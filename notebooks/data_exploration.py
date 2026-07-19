import pandas as pd
df = pd.read_csv("data/products.csv")
print("Head : \n", df.head())
print("columns : \n", df.columns)
print("Info : \n", df.info())