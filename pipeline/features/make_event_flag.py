import pandas as pd

# 引数にprefix, csvファイルへのパスの文字列とdfを受け取って、event_flagを作成する関数
# prefixは万博とirを区別するために渡す
def make_event_flag(prefix, csv_path, df):
    # csvファイルの読み込み
    df_eve = pd.read_csv(csv_path)
    # 区とイベントの種類でグループ化し、重複する場合はイベントが一番初めに起こった年を抜き出す
    df_tmp = df_eve.groupby(['municipality','event_type'])['year'].min().reset_index()
    # 行に区、列にイベントの種類を持つピボットテーブルを作成、後にdfと結合するため行を列化させる(reset_index)
    df_year = pd.pivot_table(df_tmp, values='year', index='municipality', columns='event_type', aggfunc='min').reset_index()
    # dfとdf_yearを、区名をキーとして左結合
    df = pd.merge(df, df_year, how='left', on='municipality')
    # 取引年が宣伝年より後であればTrue、そうでないならFalseという出力を数字にする
    df[f'{prefix}_announcement_flag'] = (df['transaction_year'] >= df['announcement']).fillna(False).astype(int)
    # 開発開始、開発終了、イベント実施のタイミングについても同様の処理を行う
    df[f'{prefix}_development_start_flag'] = (df['transaction_year'] >= df['development_start']).fillna(False).astype(int)
    df[f'{prefix}_development_completion_flag'] = (df['transaction_year'] >= df['development_completion']).fillna(False).astype(int)
    df[f'{prefix}_implementation_flag'] = (df['transaction_year'] >= df['implementation']).fillna(False).astype(int)
    # 不要な列を削除したdfを返す
    return df.drop(['announcement', 'development_start', 'development_completion', 'implementation'], axis=1)
