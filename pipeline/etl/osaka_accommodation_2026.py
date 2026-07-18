import pandas as pd
from pathlib import Path
from google.cloud import bigquery

# クライアントの初期化とIDの設定
project_id = 'mlit-property-price-prediction'
dataset_id = 'raw_zone'
table_name = 'osaka_accommodations'
table_id = f'{project_id}.{dataset_id}.{table_name}'

client = bigquery.Client(project=project_id)

# データセットが存在しない場合は自動で作成する
dataset_ref = bigquery.DatasetReference(project_id, dataset_id)
try:
    client.get_dataset(dataset_ref)
except Exception:
    dataset = bigquery.Dataset(dataset_ref)
    dataset.location = "asia-northeast1"  # 東京リージョンを指定（US等でも可）
    client.create_dataset(dataset)

# ロードジョブの設定
job_config = bigquery.LoadJobConfig(
    autodetect=True,
    create_disposition=bigquery.CreateDisposition.CREATE_IF_NEEDED,
    write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
)
    
# Path指定を行い、どのOSでも問題なくdfを作成可能に
raw_data_accom_csv = Path('data/raw/Osaka_Accommodation_2026/ketsugo.csv')
df = pd.read_csv(raw_data_accom_csv, encoding="utf-8-sig")

# dfの列名を確認
#print(df.columns)

# 辞書の作成
rename_dict = {
    "業種":"industry",
    "施設名称":"facility_name",
    "施設所在地":"facility_location",
    "緯度":"latitude",
    "経度":"longitude"
}

# 列名の一括置換を実行
df = df.rename(columns=rename_dict)

# BQ側にdfを出力
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()
