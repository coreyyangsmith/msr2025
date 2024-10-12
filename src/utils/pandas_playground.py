import pandas as pd

path1 = "data/cve_lifetimes.csv"
path2 = "data/cve_lifetimes_updated.csv"
path3 = "data/cve_lifetimes_gh_filtered.csv"

df1 = pd.read_csv(path1)
df2 = pd.read_csv(path2)
df3 = pd.read_csv(path3)


print(df1.count())
print(df2.count())
print(df3.count())
