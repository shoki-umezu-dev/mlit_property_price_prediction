import pandas as pd
from google.cloud import bigquery

def load_base_data():
    # BigQueryクライントのインスタンス化
    client =  bigquery.Client()

    # 各tableを読み込むためのQueryを作成
    query_pref = """
    SELECT *
    FROM `mlit-property-price-prediction.silver_zone.osaka_pref`
    """

    query_tourists = """
    SELECT *
    FROM `mlit-property-price-prediction.silver_zone.osaka_foreign_tourists`
    """

    query_residents = """
    SELECT *
    FROM `mlit-property-price-prediction.silver_zone.osaka_foreign_residents`
    """

    query_accommodations = """
    SELECT *
    FROM `mlit-property-price-prediction.silver_zone.osaka_accommodations`
    """

    # df化
    df_pref = client.query(query=query_pref).to_dataframe()
    df_tourists = client.query(query=query_tourists).to_dataframe()
    df_residents = client.query(query=query_residents).to_dataframe()
    df_accommodations = client.query(query=query_accommodations).to_dataframe()

    # df同士の結合
    df_tmp1 = pd.merge(df_pref, df_tourists, how='left', left_on='transaction_year', right_on='year')
    df_tmp1 = df_tmp1.drop(columns='year')
    df_tmp2 = pd.merge(df_tmp1, df_residents, how='left', left_on=['municipality', 'transaction_year'], right_on=['municipality', 'year'])
    df_tmp2 = df_tmp2.drop(columns='year')
    df = pd.merge(df_tmp2, df_accommodations, how='left', on='municipality')

    return df



