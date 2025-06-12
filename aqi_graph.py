import os
from datetime import datetime

import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib import colors
from descartes import PolygonPatch
from app.helper import aqi_helper as helper
import boto3


GRAPH_BUCKET_NAME = os.getenv('GRAPH_BUCKET_NAME', '/tmp')
TMP_DIR = os.getenv('TMP', '/tmp')
current_path = os.path.abspath(os.path.dirname(__file__))


def graph_gen(filename, values):
    path = os.path.join(current_path, "../geoFile/COUNTY_MOI_1080726.shp")
    town_shp = gpd.read_file(path, encoding='utf-8')
    df = pd.DataFrame(values)
    df['value'].astype(float)

    eaststation = pd.DataFrame()
    strEast = ['冬山', '花蓮', '關山', '臺東', '恆春']
    for i, eastSite in enumerate(strEast):
        select = df[df['site'] == eastSite]
        select['sortIndex'] = i
        eaststation = pd.concat([eaststation, select], axis=0)
    eaststation = eaststation.sort_values(by='sortIndex', ascending=True)

    eaststation['value'] = eaststation['value'].astype(int)
    eaststation['lng'] = eaststation['lng'].astype(float)
    eaststation['lat'] = eaststation['lat'].astype(float)

    i = len(eaststation) - 2
    tempPm = round((eaststation.iloc[i]['value'] + eaststation.iloc[i + 1]['value']) / 2)
    tempPx = round((eaststation.iloc[i]['lng'] + eaststation.iloc[i + 1]['lng']) / 2) - 25 / 350.92733
    tempPy = round((eaststation.iloc[i]['lat'] + eaststation.iloc[i + 1]['lat']) / 2)
    tempIndex = (eaststation.iloc[i]['sortIndex'] + eaststation.iloc[i + 1]['sortIndex']) / 2
    temp = pd.DataFrame.from_dict({
        'site': '虛擬',
        'lng': [tempPx],
        'lat': [tempPy],
        'value': [tempPm],
        'sortIndex': [tempIndex]})
    eaststation = pd.concat([eaststation, temp], axis=0)
    temp = pd.DataFrame.from_dict({
        'site': '虛擬',
        'lng': [tempPx],
        'lat': [tempPy],
        'value': [tempPm]})
    df = pd.concat([df, temp], axis=0)
    eaststation = eaststation.sort_values(by='sortIndex', ascending=True)

    for i in range(len(eaststation) - 1):
        tempPm = (eaststation.iloc[i]['value'] + eaststation.iloc[i + 1]['value']) / 2
        tempPx = (eaststation.iloc[i]['lng'] + eaststation.iloc[i + 1]['lng']) / 2
        tempPy = (eaststation.iloc[i]['lat'] + eaststation.iloc[i + 1]['lat']) / 2
        temp = pd.DataFrame.from_dict({
            'site': '虛擬',
            'lng': [tempPx],
            'lat': [tempPy],
            'value': [tempPm]})
        df = pd.concat([df, temp], axis=0)

    gdf = gpd.GeoDataFrame(
        df, geometry=gpd.points_from_xy(df.lng, df.lat))
    gdf.crs = {'init': 'epsg:3826'}
    gdf['geometry'] = gdf.geometry.buffer(0.015)

    iInterval = (122.7 - 119) / 120
    jInterval = (25.5 - 21.8) / 120
    result = []
    index1 = 0
    index2 = 0
    for j in np.arange(25.5, 21.8, -jInterval):
        nested = []
        for i in np.arange(119, 122.7, iInterval):
            point = {'x': i, 'y': j}
            if helper.is_in_area(index1, index2):
                nested.append(helper.calc_idw_value(point, df))
            else:
                nested.append(-1)
            index2 += 1
        result.append(nested)
        index1 += 1
        index2 = 0
    result = np.array(result)

    fig, ax = plt.subplots(1)
    ax = town_shp.plot(ax=ax, color='none')
    plt.axis('off')
    ax.set_facecolor("none")

    # create discrete colormap
    cmap = colors.ListedColormap(
        ['white', '#0000FF', '#001AFF', '#0033FF', '#004DFF', '#0066FF', '#0080FF', '#0099FD', '#00B3FB', '#00CCF9',
         '#00E6F7', '#00FFF5', '#20FFD7', '#40FFB9', '#60FF9B', '#80FF7D', '#9FFF5F', '#BFFF41', '#DFFF23', '#FFFF00',
         '#FFFF00', '#FFFF00', '#FFF800', '#FFF000', '#FFE900', '#FFE100', '#FFDA00', '#FFD200', '#FFCB00', '#FFC300',
         '#FFBC00', '#FFB400', '#FFAD00', '#FFA500', '#FF9E00', '#FF9600', '#FF8F00', '#FF8700', '#FF8000', '#FF7800',
         '#FF7100', '#FF6900', '#FF6200', '#FF5A00', '#FF5300', '#FF4B00', '#FF4400', '#FF3C00', '#FF3500', '#FF2D00',
         '#FF2600', '#FF1E00', '#FF1700', '#FF0F00', '#FF0800', '#FF0000', '#FF0000', '#F80000', '#F10000', '#EB0000',
         '#E40000', '#DD0000', '#D60000', '#CF0000', '#C90000', '#C20000', '#BB0000', '#B40000', '#AD0000', '#A70000',
         '#A00000', '#990000', '#9C000F', '#A0001F', '#A3002E', '#A7003D', '#AA004D', '#AD005C', '#B1006B', '#B4007A',
         '#B8008A', '#BB0099', '#BE009E', '#C200A3', '#C500A8', '#C900AD', '#CC00B2', '#CF00B8', '#D300BD', '#D600C2',
         '#DA00C7', '#DD00CC', '#E000D1', '#E400D6', '#E700DB', '#EB00E0', '#EE00E5', '#F100EB', '#F500F0', '#F800F5',
         '#FC00FA', '#FF00FF'])
    bounds = [-1, -0.1, 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26,
              27, 28,
              29, 30, 31, 32, 33, 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54,
              55,
              56, 57, 58, 59, 60, 61, 62, 63, 64, 65, 66, 67, 68, 69, 70, 71, 72, 73, 74, 75, 76, 77, 78, 79, 80, 81,
              82,
              83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94, 95, 96, 97, 98, 99, 100, 1000]
    norm = colors.BoundaryNorm(bounds, cmap.N)

    x1, x2, y1, y2 = 119 - iInterval * 0.5, 122.7 - iInterval * 0.5, 21.8 + jInterval * 0.5, 25.5 + jInterval * 0.5

    for index, row in town_shp.iterrows():
        if (row['COUNTYNAME'] == '連江縣') or (row['COUNTYNAME'] == '金門縣') or (row['COUNTYNAME'] == '澎湖縣'):
            if row['COUNTYNAME'] == '澎湖縣':
                ta_town_shp = town_shp[town_shp['COUNTYNAME'] == '澎湖縣']
                value = df[df['site'] == '馬公']['value'].values
                if len(value) > 0:
                    color = helper.set_color(value[0])
                else:
                    color = 'white'
                ta_town_shp.plot(ax=ax, color=color, edgecolor='#898990', linewidth=0.4)
                continue
            else:
                continue
        patch = PolygonPatch(row['geometry'], facecolor='none', edgecolor='#323333', linewidth=0.6)
        ax.add_patch(patch)
        ax.imshow(result, cmap=cmap, norm=norm, extent=(x1, x2, y1, y2), clip_path=patch, clip_on=True)

    #  連江
    ax2 = fig.add_axes([0.1, 0.63, 0.08, 0.12])
    ta_town_shp = town_shp[town_shp['COUNTYNAME'] == '連江縣']
    value = df[df['site'] == '馬祖']['value'].values
    if len(value) > 0:
        color = helper.set_color(value[0])
    else:
        color = 'white'
    ax2 = ta_town_shp.plot(ax=ax2, color=color, edgecolor='#898990', linewidth=0.4)
    ax2.get_xaxis().set_visible(False)
    ax2.get_yaxis().set_visible(False)
    # sub region of the original image
    x1, x2, y1, y2 = 119.88, 120.05, 26.12, 26.32
    ax2.set_xlim(x1, x2)
    ax2.set_ylim(y1, y2)

    # 金門
    ax3 = fig.add_axes([0.1, 0.35, 0.1, 0.48])
    ta_town_shp = town_shp[town_shp['COUNTYNAME'] == '金門縣']
    value = df[df['site'] == '金門']['value'].values
    if len(value) > 0:
        color = helper.set_color(value[0])
    else:
        color = 'white'
    ax3 = ta_town_shp.plot(ax=ax3, color=color, edgecolor='#898990', linewidth=0.4)
    ax3.get_xaxis().set_visible(False)
    ax3.get_yaxis().set_visible(False)
    x1, x2, y1, y2 = 118.15, 118.55, 24.35, 24.6
    ax3.set_xlim(x1, x2)
    ax3.set_ylim(y1, y2)

    # 測站點
    select = (gdf['site'] != '虛擬') & (gdf['site'] != '屏東(琉球)') & (gdf['site'] != '馬公')
    ax4 = gdf[select].plot(ax=ax, edgecolor='#666666', facecolor='none', linewidth=1.5)
    ax4.set_xlim(119.2, 122.08)
    ax4.set_ylim(21.85, 25.4)
    ax4.get_xaxis().set_visible(False)
    ax4.get_yaxis().set_visible(False)

    fig.set_size_inches(1059.84 / 72, 1186.56 / 72)
    plt.gca().xaxis.set_major_locator(plt.NullLocator())
    plt.gca().yaxis.set_major_locator(plt.NullLocator())
    plt.subplots_adjust(top=1, bottom=0, right=1, left=0, hspace=0, wspace=0)
    plt.margins(0, 0)

    SOURCE_FILENAME = f"{TMP_DIR}/{filename}.png"
    fig.savefig(SOURCE_FILENAME, format='png', transparent=True, dpi=72, pad_inches=0)

    data_category = 'pm25'
    ENVIRONMENT = os.getenv('ENV', 'development')
    if ENVIRONMENT == 'production':
        S3_PATH = f'{data_category}/idw_map/{filename}.png'
    else:
        S3_PATH = f'dev/{data_category}-{filename}.png'

    time = datetime.strptime(filename, '%Y%m%d%H%M')
    upload_to_s3(SOURCE_FILENAME, S3_PATH, ENVIRONMENT, data_category, time)

    im = plt.imread(os.path.join(current_path, "title.png"))
    title_ax = fig.add_axes([0.05, 0.46, 0.4, 0.5], anchor='NW', zorder=1)
    title_ax.imshow(im)
    title_ax.text(0, 200, time.strftime('%Y.%m.%d  %H:%M'), fontsize=34, color='#717071',
                  fontweight='bold')
    title_ax.axis('off')
    SOURCE_FILENAME = f"{TMP_DIR}/tcepb-{filename}.png"
    fig.savefig(SOURCE_FILENAME, format='png', transparent=True, dpi=72, pad_inches=0, facecolor=fig.get_facecolor())
    plt.close(fig)
    if ENVIRONMENT == 'production':
        S3_PATH = f'{data_category}/tcepb/{filename}.png'
    else:
        S3_PATH = f'dev/tcepb/{data_category}-{filename}.png'
    upload_to_s3(SOURCE_FILENAME, S3_PATH, ENVIRONMENT, data_category, time)


def upload_to_s3(SOURCE_FILENAME, S3_PATH, ENVIRONMENT, data_category, time, update_latest_time=True):
    # Create an S3 client
    S3 = boto3.client('s3')

    S3.upload_file(SOURCE_FILENAME, GRAPH_BUCKET_NAME, S3_PATH, ExtraArgs={'ACL': 'public-read'})
    os.remove(SOURCE_FILENAME)

    if ENVIRONMENT == 'production' and update_latest_time:
        local_path = f'{TMP_DIR}/latest_data_time_{data_category}'
        S3.download_file(GRAPH_BUCKET_NAME, f'{data_category}/latest_data_time', local_path)

        timetext = time.strftime("%Y-%m-%d  %H:%M")
        with open(local_path, 'r') as file:
            content = file.read()
            content = content.split(',')
            with open(local_path, 'w+') as file1:
                if len(content) < 1:
                    content.append(timetext)
                if timetext not in content:
                    content.append(timetext)
                if len(content) > 48:
                    content = content[len(content) - 48:]
                content.sort()
                file1.write(",".join(content))
        S3.upload_file(local_path, GRAPH_BUCKET_NAME, f'{data_category}/latest_data_time')
        os.remove(local_path)
