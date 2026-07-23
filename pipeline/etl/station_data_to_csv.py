import math
import time

import pandas as pd
import requests
from google.cloud import bigquery
from dotenv import load_dotenv
import os

# .envからAPIキーの取得
load_dotenv()
api_key = os.getenv("GOOGLE_MAPS_API_KEY")

GEOCODE_URL = "https://maps.googleapis.com/maps/api/geocode/json"
YUMESHIMA_STATION = "夢洲駅, 大阪府"


def geocode_station(query):
    """駅名(検索クエリ文字列)から緯度経度を取得する。見つからなければNoneを返す。"""
    res = requests.get(GEOCODE_URL, params={"address": query, "key": api_key})
    res.raise_for_status()
    data = res.json()
    if data["status"] != "OK" or not data["results"]:
        return None
    location = data["results"][0]["geometry"]["location"]
    return location["lat"], location["lng"]


def haversine_distance_km(lat1, lng1, lat2, lng2):
    """2地点間の直線距離(km)をハーバサイン公式で計算する。"""
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlambda / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))


def main():
    # BigQueryクライアントのインスタンス化
    client = bigquery.Client()

    query_pref = """
    SELECT DISTINCT nearest_station
    FROM `mlit-property-price-prediction.silver_zone.osaka_pref`
    """
    df_pref = client.query(query=query_pref).to_dataframe()
    stations = df_pref["nearest_station"].unique()

    # 夢洲駅の緯度経度を取得(基準点)
    yumeshima_coords = geocode_station(YUMESHIMA_STATION)
    if yumeshima_coords is None:
        raise RuntimeError("夢洲駅のジオコーディングに失敗しました")
    yumeshima_lat, yumeshima_lng = yumeshima_coords

    # 各駅ごとに緯度経度を取得し、夢洲駅までの直線距離を計算
    results = []
    for station in stations:
        query = f"{station}駅, 大阪府"
        coords = geocode_station(query)
        if coords is None:
            print(f"WARNING: ジオコーディング失敗: {station}")
            results.append({
                "nearest_station": station,
                "latitude": None,
                "longitude": None,
                "distance_to_yumeshima_km": None,
            })
        else:
            lat, lng = coords
            distance = haversine_distance_km(lat, lng, yumeshima_lat, yumeshima_lng)
            results.append({
                "nearest_station": station,
                "latitude": lat,
                "longitude": lng,
                "distance_to_yumeshima_km": distance,
            })
        time.sleep(0.1)  # APIへの負荷を抑える

    df_result = pd.DataFrame(results)
    out_path = "data/raw/station_distance.csv"
    df_result.to_csv(out_path, index=False)
    print(f"saved: {out_path} ({len(df_result)} stations, {df_result['distance_to_yumeshima_km'].isna().sum()} failed)")


if __name__ == "__main__":
    main()
