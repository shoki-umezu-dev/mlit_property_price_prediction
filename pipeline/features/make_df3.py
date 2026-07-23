import pandas as pd
import numpy as np
from pipeline.features.make_event_flag import make_event_flag
from pathlib import Path


years_list = [2026, 2027, 2028, 2029, 2030]
quarters_list =[1, 2, 3, 4]

def make_df3(df):
    # 受け取ったdfのコピーを作成し、不要な列を落とす
    df_cp = df.copy()
    df_cp = df_cp.drop(['transaction_price', 'price_per_sqm', 'transaction_year', 'transaction_quarter'], axis=1)

    # 取引年、取引四半期を各取引にランダムに当てはめる
    df_cp['transaction_year'] = np.random.choice(years_list, size=len(df_cp))
    df_cp['transaction_quarter'] = np.random.choice(quarters_list, size=len(df_cp))

    # ラグ特徴量と時間軸のある外部データを2025年時点で上書き
    df_2025 = df[df['transaction_year'] == 2025].groupby('municipality')[['actual_foreign_guests',
       'foreign_male_counts', 'foreign_female_counts', 'total_counts',
       'include_foreign_household_counts', 'median_price_1year_ago', 'median_price_2year_ago',
       'median_price_3year_ago', 'median_price_4year_ago',
       'median_price_5year_ago']].median().reset_index()
    
    df_cp = df_cp.drop(['actual_foreign_guests',
       'foreign_male_counts', 'foreign_female_counts', 'total_counts',
       'include_foreign_household_counts', 'median_price_1year_ago', 'median_price_2year_ago',
       'median_price_3year_ago', 'median_price_4year_ago',
       'median_price_5year_ago'], axis=1)
    
    df_cp = pd.merge(df_cp, df_2025, how='left', on='municipality')

    # event_flagの作成
    data_raw_osaka_events = Path('../data/raw/Osaka_Events')
    df_cp = make_event_flag('expo', data_raw_osaka_events/'expo_event_time_series.csv', df_cp)
    df_cp = make_event_flag('ir', data_raw_osaka_events/'ir_event_time_series.csv', df_cp)

    return df_cp
