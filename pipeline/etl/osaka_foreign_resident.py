import pandas as pd
from pathlib import Path
from google.cloud import bigquery

# クライアントの初期化とIDの設定
project_id = 'mlit-property-price-prediction'
dataset_id = 'raw_zone'
table_name = 'osaka_foreign_residents'
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
raw_data_dir = Path('./data/raw/Osaka_Pref_foreign_resident')

# CSVファイルのリストを作成
list_csv = list(raw_data_dir.glob("*.csv"))

# 文字コードをshift_jisに指定したdfのリストを作成
df_list = [pd.read_csv(file, encoding="utf-8-sig") for file in list_csv]

# df_listから1つずつ取り出してyearを追加し、2017年の不明列の削除と2025年の計列の作成、合計行以外の抽出を行う
foreign_resident_list = []
for i, (foreign_resident, file) in enumerate(zip(df_list, list_csv)):
    year = int(str(file.name)[:4])
    foreign_resident['year'] = year
    if year == 2017:
        foreign_resident = foreign_resident.drop(columns="Unnamed: 5")
        foreign_resident_list.append(foreign_resident[~foreign_resident['区名'].str.contains("合計")])
    elif year == 2018:
        rename_dict = {
    "男": "外国人男",
    "女": "外国人女",
    "世帯数": "外国人を含む世帯数"
    }
        foreign_resident = foreign_resident.rename(columns=rename_dict)
        foreign_resident_list.append(foreign_resident[~foreign_resident['区名'].str.contains("合計")])
    elif year == 2025:
        foreign_resident['計'] = foreign_resident['外国人男'] + foreign_resident['外国人女']
        foreign_resident_list.append(foreign_resident[~foreign_resident['区名'].str.contains("合計")][['区名', '外国人男', '外国人女', '計', '外国人を含む世帯数', 'year']])
    else:
        foreign_resident_list.append(foreign_resident[~foreign_resident['区名'].str.contains("合計")])

# 読み込んだdfのカラム名の確認
#print(foreign_resident_list[0].columns.tolist())
#raw = pd.read_csv(list_csv[0], encoding="utf-8-sig")
#print(raw.head(10))

# dfのリストを行方向に結合する
df = pd.concat(foreign_resident_list, axis=0)

# カラム名の日本語と英語を対応させた辞書の作成
rename_dict = {
"区名": "municipality",
"外国人男": "foreign_male_counts",
"外国人女": "foreign_female_counts",
"計": "total_counts", 
"外国人を含む世帯数": "include_foreign_household_counts",
}

# 列名の一括置換を実行
df = df.rename(columns=rename_dict)

# BQ側にdfを出力
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()
