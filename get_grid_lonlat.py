import pandas as pd

# 定義格點範圍與間距
lon_start, lon_end = 119, 122.7
lat_start, lat_end = 21.8, 25.5
num_cols = 120  # x 軸格數
num_rows = 120  # y 軸格數

iInterval = (lon_end - lon_start) / num_cols
jInterval = (lat_end - lat_start) / num_rows

# 建立格點列表
grid_data = []
for j in range(num_rows):
    for i in range(num_cols):
        lon = lon_start + i * iInterval
        lat = lat_start + j * jInterval
        grid_data.append((len(grid_data), lon, lat))

# 存成 CSV
df = pd.DataFrame(grid_data, columns=["id", "lon", "lat"])
df.to_csv("grid.csv", index=False, encoding="utf-8-sig")
print("✅ grid.csv 已建立，共有格點數：", len(df))
