import pandas as pd

def make_lag_features(df):
    df.loc[df['area_no_max_limit_flag'] == 1, 'area_sqm'] = 2000
    df['price_per_sqm'] = df['transaction_price'] / df['area_sqm'] 
    df_tmp = df.groupby(['municipality', 'transaction_year'])['price_per_sqm'].median().reset_index()
    df_tmp = df_tmp.sort_values(['municipality', 'transaction_year'])
    df_tmp['median_price_1year_ago'] = df_tmp.groupby("municipality")["price_per_sqm"].shift(1)
    df_tmp['median_price_2year_ago'] = df_tmp.groupby("municipality")["price_per_sqm"].shift(2)
    df_tmp['median_price_3year_ago'] = df_tmp.groupby("municipality")["price_per_sqm"].shift(3)
    df_tmp['median_price_4year_ago'] = df_tmp.groupby("municipality")["price_per_sqm"].shift(4)
    df_tmp['median_price_5year_ago'] = df_tmp.groupby("municipality")["price_per_sqm"].shift(5)
    df = pd.merge(df, df_tmp.drop('price_per_sqm', axis=1), how='left', on=['municipality', 'transaction_year'])
    return df


