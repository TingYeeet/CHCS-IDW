import os
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

import matplotlib.pyplot as plt

def plot_grid_overlay(taiwan_map, grid_gdf, grid_values):
    """
    視覺化台灣地圖與有效格點疊圖
    """
    # 轉換為 GeoSeries（只取有效值）
    valid_mask = grid_values > -1
    valid_points = grid_gdf[valid_mask]

    # 畫圖
    fig, ax = plt.subplots(figsize=(10, 12))
    
    # 畫底圖（行政區）
    taiwan_map.plot(ax=ax, edgecolor='black', facecolor='none', linewidth=0.5)

    # 畫有效格點
    valid_points.plot(ax=ax, color='red', markersize=5, alpha=0.6, label='有效格點')

    # 標題與圖例
    ax.set_title('台灣行政區與有效 PM2.5 格點分布', fontsize=14)
    ax.legend()
    plt.xlabel('經度')
    plt.ylabel('緯度')
    plt.grid(True)
    plt.tight_layout()
    plt.show()

iInterval = (122.7 - 119) / 120
jInterval = (25.5 - 21.8) / 120


# 載入台灣鄉鎮圖層
taiwan_map = gpd.read_file("TOWN_MOI_1131028.gml")
taiwan_map = taiwan_map.set_crs("EPSG:3824")  # TWD97經緯度
taiwan_map = taiwan_map.to_crs("EPSG:4326")   # 轉換為WGS84經緯度以便疊合

# 載入格點座標（已知為 WGS84 經緯度）
grid_df = pd.read_csv("grid.csv")  # 假設這個CSV裡有經緯度欄位：lon, lat
geometry = [Point(xy) for xy in zip(grid_df["lon"], grid_df["lat"])]

grid_points = []
for j in range(120):
    for i in range(120):
        lon = 119 + i * iInterval
        lat = 25.5 - j * jInterval  # 🔁 從北往南扣
        grid_points.append(Point(lon, lat))

grid_gdf = gpd.GeoDataFrame(geometry=grid_points, crs="EPSG:4326")

# 結果列表
results = []

# 處理每年的每週資料
for year in range(2016, 2020):
    for month in range(1, 13):
        grid_path = f'./grid_csv_month/{year}_month_{month}.csv'
        if not os.path.exists(grid_path):
            continue

        # 讀取格點數值，略過橫列編號（第一行）
        grid_values = pd.read_csv(grid_path, skiprows=1, header=None).values.flatten()

        # plot 當前週的格點分布
        # plot_grid_overlay(taiwan_map, grid_gdf, grid_values)
        
        # 檢查是否格點數量對得上
        if len(grid_values) != len(grid_gdf):
            print(f"⚠️ 資料長度不符：{grid_path} ({len(grid_values)} vs {len(grid_gdf)})")
            continue

        # 篩選有效值格點（不為 -1）
        valid_mask = grid_values != -1
        if valid_mask.sum() == 0:
            print(f"❌ 全部為 -1：{grid_path}")
            continue

        grid_subset = grid_gdf[valid_mask].copy()
        grid_subset["value"] = grid_values[valid_mask]

        # 疊合鄉鎮圖層
        joined = gpd.sjoin(grid_subset, taiwan_map, predicate='within', how='inner')
        grouped = joined.groupby('名稱')

        for town, group in grouped:
            town_geom = taiwan_map.loc[taiwan_map['名稱'] == town, 'geometry'].values[0]

            # ✅ 用有效格點 subset 來計算總覆蓋格數
            total_cells = grid_subset.geometry.intersects(town_geom).sum()
            coverage = len(group) / total_cells if total_cells else 0

            # print(f'{town} - 有效格點: {len(group)} / 鄉鎮內總有效格點: {total_cells} → 覆蓋率: {coverage:.2f}')

            if coverage >= 0.5:
                avg_val = group['value'].mean() * 30
                results.append({
                    'town': town,
                    'year': year,
                    'month': month,
                    'PM2.5': round(avg_val, 2)
                })

        print(f'{year} 年第 {month} 月資料計算完成')


# 輸出 CSV
if results:
    result_df = pd.DataFrame(results)
    result_df.to_csv("PM25_monthly_by_town.csv", index=False, encoding="utf-8-sig")
    print("✅ 輸出完成：PM25_monthly_by_town.csv")
else:
    print("⚠️ 無有效結果輸出")
