import pandas as pd
import geopandas as gpd
from shapely.geometry import Point
import os

# 定義縣市代碼與對應區域
region_map = {
    '北北基桃竹苗': ['臺北市', '新北市', '基隆市', '桃園市', '新竹市', '新竹縣', '苗栗縣'],
    '中彰投': ['臺中市', '彰化縣', '南投縣'],
    '雲嘉南': ['雲林縣', '嘉義市', '嘉義縣', '臺南市'],
    '高屏': ['高雄市', '屏東縣'],
    '宜花東': ['宜蘭縣', '花蓮縣', '臺東縣']
}

# 將縣市轉成區域對應表
def assign_region(county):
    for region, counties in region_map.items():
        if any(c in county for c in counties):
            return region
    return '其他'

# 載入台灣鄉鎮圖層
taiwan_map = gpd.read_file("TOWN_MOI_1131028.gml")
taiwan_map = taiwan_map.set_crs("EPSG:3824")  # TWD97經緯度
taiwan_map = taiwan_map.to_crs("EPSG:4326")   # 轉換為WGS84經緯度以便疊合
taiwan_map["region"] = taiwan_map["名稱"].apply(assign_region)

# 建立格點 GeoDataFrame
iInterval = (122.7 - 119) / 120
jInterval = (25.5 - 21.8) / 120
grid_points = [Point(119 + i * iInterval, 25.5 - j * jInterval) for j in range(120) for i in range(120)]
grid_gdf = gpd.GeoDataFrame(geometry=grid_points, crs="EPSG:4326")

# 結果儲存
results = []

# 處理每年每月
for year in range(2016, 2020):
    for month in range(1, 13):
        grid_path = f'./grid_csv_month/{year}_month_{month}.csv'
        if not os.path.exists(grid_path):
            continue

        grid_values = pd.read_csv(grid_path, skiprows=1, header=None).values.flatten()
        if len(grid_values) != len(grid_gdf):
            print(f"⚠️ 資料長度不符：{grid_path} ({len(grid_values)} vs {len(grid_gdf)})")
            continue

        valid_mask = grid_values != -1
        if valid_mask.sum() == 0:
            print(f"❌ 全部為 -1：{grid_path}")
            continue

        grid_subset = grid_gdf[valid_mask].copy()
        grid_subset["value"] = grid_values[valid_mask]

        # 疊合行政區
        joined = gpd.sjoin(grid_subset, taiwan_map[["geometry", "region"]], predicate='within', how='inner')
        grouped = joined.groupby('region')

        for region, group in grouped:
            avg_val = group["value"].mean() * 30
            results.append({
                "region": region,
                "year": year,
                "month": month,
                "PM2.5": round(avg_val, 2)
            })

        print(f"{year} 年第 {month} 月資料計算完成")

# 輸出結果
if results:
    result_df = pd.DataFrame(results)
    result_df.to_csv("PM25_monthly_by_region.csv", index=False, encoding="utf-8-sig")
    print("✅ 輸出完成：PM25_monthly_by_region.csv")
else:
    print("⚠️ 無有效結果輸出")
