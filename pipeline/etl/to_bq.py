import uuid
import pandas as pd
from pathlib import Path
from google.cloud import bigquery

# クライアントの初期化とIDの設定
project_id = 'mlit-property-price-prediction'
dataset_id = 'raw_zone'
table_name = 'osaka_pref'
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
raw_data_dir = Path('./data/raw')
# csvファイルのリストを作成
list_csv = list(raw_data_dir.glob("*.csv"))
# 文字コードをshift_jisに指定したdfのリストを作成
df_list = [pd.read_csv(file, encoding="cp932", dtype=str) for file in list_csv]
# dfのリストを行方向に結合する
df = pd.concat(df_list, axis=0)

# 【追加】Pandas側で一意のUUIDキー（サロゲートキー）列を生成
df["id"] = [str(uuid.uuid4()) for _ in range(len(df))]

# カラム名の日本語と英語を対応させた辞書の作成
rename_dict = {
    '種類': 'type',
    '価格情報区分': 'price_info_class',
    '市区町村コード': 'municipality_code',
    '都道府県名': 'prefecture',
    '市区町村名': 'municipality',
    '地区名': 'district',
    '最寄駅：名称': 'nearest_station',
    '最寄駅：距離（分）': 'time_to_station',
    '取引価格（総額）': 'transaction_price',
    '間取り': 'layout',
    '面積（㎡）': 'area_sqm',
    '建築年': 'building_year',
    '建物の構造': 'structure',
    '用途': 'use',
    '今後の利用目的': 'future_use',
    '都市計画': 'city_planning',
    '建ぺい率（％）': 'coverage_ratio',
    '容積率（％）': 'floor_area_ratio',
    '取引時期': 'transaction_period',
    '改装': 'renovation',
    '取引の事情等': 'transaction_notes'
}

# 列名の一括置換を実行
df = df.rename(columns=rename_dict)

# 列の並び替え（idを先頭に持ってくる）
cols = ["id"] + [col for col in df.columns if col != "id"]
df = df[cols]

# BQ側にdfを出力
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()
