import pandas as pd

df = pd.read_csv('data/tokens.csv')
# print datatype of each column
print(df.iloc[0][1] == "GTPL-BL")