import uuid
import pandas as pd
from pathlib import Path
from google.cloud import bigquery

# クライアントの初期化とIDの設定
project_id = 'mlit-property-price-prediction'
dataset_id = 'raw_zone'
table_name = 'osaka_foreign_tourists'
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
raw_data_dir = Path('./data/raw/Osaka_Pref_foreign_tourists')

# エクセルファイルのリストを作成
list_xls = list(raw_data_dir.glob("*.xls"))
list_xlsx = list(raw_data_dir.glob("*.xlsx"))
list_excel = list_xls + list_xlsx

# エクセルファイルのシート確認
#xls = [pd.ExcelFile(file) for file in list_excel]

#for file, xl in zip(list_excel, xls):
    #print(file.name, xl.sheet_names)

# 文字コードをshift_jisに指定したdfのリストを作成
df_list = [pd.read_excel(file, sheet_name="第3表(年計)", header=None) for file in list_excel]

# 読み込んだdfのカラム名の確認
#print(df_list[0].columns.tolist())
#raw = pd.read_excel(list_excel[0], sheet_name="第3表(年計)", header=None)
#print(raw.head(10))

# 大阪府が各ファイルに含まれているか(半角などが必要ないか)確認
#for file in list_excel:
    #df = pd.read_excel(file, sheet_name="第3表(年計)", header=None)
    #print(file.name, (df[0] == "大阪府").sum())

#df = pd.read_excel(list_excel[0], sheet_name="第3表(年計)", header=None)  # 201400.xlsを指すもの
#print(df[df[0].astype(str).str.contains("大阪", na=False)][0])

#df = pd.read_excel(raw_data_dir / "201800.xlsx", sheet_name="第3表(年計)", header=None)
#print(df[df[0].astype(str).str.contains("大阪", na=False)][0])

# df_listから大阪府の実宿泊者数のデータに絞ってyearを追加する
df_osaka_list = []
for i, (df_osaka, file) in enumerate(zip(df_list, list_excel)):
    df_osaka_pref = df_osaka[df_osaka[0].astype(str).str.contains("大阪府", na=False)][[0, 13]]
    df_osaka_pref['year'] = int(str(file.name)[:4])
    df_osaka_list.append(df_osaka_pref)

#for df_osaka in df_osaka_list:
    #print(len(df_osaka))


# dfのリストを行方向に結合する
df = pd.concat(df_osaka_list, axis=0)

# カラム名の日本語と英語を対応させた辞書の作成
rename_dict = {
0: "facility_location",
13: "actual_foreign_guests",
"year": "year",
}

# 列名の一括置換を実行
df = df.rename(columns=rename_dict)

# 列の並び替え（idを先頭に持ってくる）
cols = ["year"] + [col for col in df.columns if col != "year"]
df = df[cols]

# BQ側にdfを出力
job = client.load_table_from_dataframe(df, table_id, job_config=job_config)
job.result()
