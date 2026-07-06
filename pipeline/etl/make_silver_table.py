from pathlib import Path
from google.cloud import bigquery

# Pathの設定を行い、どのOSでも問題なくファイルを読み込めるように設定
pipe_sql_file = Path('./pipeline/sql/make_prep_data.sql')

# clientの設定
client = bigquery.Client() 

# sqlファイルの読み込み
with open(pipe_sql_file) as file:
    sql_query = file.read()

# クエリの実行
query_job = client.query(sql_query)
query_job.result()










