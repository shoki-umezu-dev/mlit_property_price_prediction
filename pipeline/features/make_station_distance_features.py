import pandas as pd


def make_station_distance_features(df, csv_path="../data/raw/station_distance.csv"):
    """最寄駅から夢洲駅までの直線距離(km)をnearest_stationをキーに結合する。"""
    df_dist = pd.read_csv(csv_path)[["nearest_station", "distance_to_yumeshima_km"]]
    df = pd.merge(df, df_dist, how="left", on="nearest_station")
    return df
