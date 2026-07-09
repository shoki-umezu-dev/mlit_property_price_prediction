from google.cloud import bigquery
import argparse

# argparseにより、外部からファイルを指定して受け取れるようにする
parser = argparse.ArgumentParser()
parser.add_argument("--sql", type=str, required=True)
args = parser.parse_args()

# Pathの設定を行い、どのOSでも問題なくファイルを読み込めるように設定
#pipe_sql_file = Path('./pipeline/sql/make_prep_data.sql')

# clientの設定
client = bigquery.Client() 

# sqlファイルの読み込み
with open(args.sql) as file:
    sql_query = file.read()

# クエリの実行
query_job = client.query(sql_query)
query_job.result()










