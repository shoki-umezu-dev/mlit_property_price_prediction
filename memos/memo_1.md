## zipファイルが解凍できない場合の処置
- ターミナルでの解決方法
    - unzip を打ち込む
    - 開けないzipファイルをドラッグする

## 20260702に行った内容
1. 環境構築(インフラ)
- GCPプロジェクト mlit-property-price-prediction を作成、BigQuery APIを有効化
- ローカルに gcloud/bq CLIが無かったため、Homebrewで Google Cloud SDK を導入
- gcloud auth application-default login でADC認証を設定
- Pythonプロジェクト管理は uv を採用（既に使用経験があったため）。.python-version=3.11 に固定
    - 意図: 後工程で使うProphet/InterpretML(EBM)/LightGBMとの互換性を考え、Pythonもpandasも最新版に飛びつかず枯れたバージョンを意識する方針
2. リポジトリ構成の設計判断
- .py（実行スクリプト）と.sql（クエリ本体）はファイルを分離する方針（保守性のため）
- notebooks/はEDA専用（01_eda.ipynb）、ETL用のコードはpipeline/etl/、SQLはpipeline/sql/に分離
    - 意図: ディレクトリ名から用途が推測できるようにする（ポートフォリオとしての可読性）
- .gitignoreに.venv/を追加

3. データ基盤(raw層)の設計判断と理由
|判断 |	内容 | 理由 |
| レイヤー分離 | raw層(生データ)とsilver層(前処理済み)を分ける | 前処理をやり直す際に生データから再スタートできるようにするため |
| 取り込み方式 | CSVを直接BigQueryにロードせず、pandasで読み込んでDataFrameとして送る | BigQueryのCSVロードジョブがcp932/Shift-JISのような文字コードを直接サポートしないため |
| 文字コード | shift_jisではなくcp932を指定 | 国交省データにNEC拡張文字が含まれ、標準shift_jisではデコードエラーになったため |
| dtype | 全列dtype=strで読み込み | raw層の「生データ保全」という目的に合わせ、pandas/BigQueryの自動型推定に委ねない |
| カラム名 | 日本語ヘッダーを英語snake_caseにリネーム。pandas側で実施 | コードは英語ベースが実務的。SQL側で行うと従量課金のBigQuery処理が1ステップ増えるため、pandas側で行うコスト判断 |
| サロゲートキー | pandas側でuuid.uuid4()を発行しid列として付与 | 将来「特定年のファイルだけ差し替え」という部分差し替え運用を想定し、既存行とキーが衝突しないようにするため。当初BigQuery側のDEFAULT GENERATE_UUID()案も検討したが、同じ目的をより単純に実現できるpandas側の方式を採用 |
| 書き込み方式 | write_disposition=WRITE_TRUNCATE | 開発中に何度再実行しても同じ結果になる(冪等性)ようにするため |
| 差し替え単位の判別 | transaction_period列で年・四半期が分かるため、専用の「ソースファイル」列は不要と判断 | 既存カラムで十分に用途を満たせるため | 

4. 実装・実行
- pipeline/etl/to_bq.py を作成し、12個のCSV（2014〜2025年、Shift-JIS系）を読み込み→結合→リネーム→キー付与→BigQueryへロード
- 依存関係のトラブルシュート: pyarrowが必要（load_table_from_dataframeの要件）
- 実行成功: raw_zone.osaka_pref テーブルにデータ投入済みを確認済み（pandas-gbqの将来的な必須化に関するFutureWarningは残存、未対応）

5. 現在地と次のステップ
raw層の構築（F-1の「取り込み」部分）は完了。次は silver層への前処理SQL の設計に入るところです（pipeline/sql/配下に実装予定）。想定される変換対象は、価格・面積等の数値CAST、time_to_stationの"30分〜60分"表記の数値化、building_yearの和暦変換、transaction_periodの年/四半期分解、欠損フラグの付与などです。この部分の方針はまだ固まっていません。


## 20260706までのまとめ
### 環境構築
- GCPプロジェクト `mlit-property-price-prediction` を作成、BigQuery API有効化
- Homebrewで Google Cloud SDK (`gcloud`, `bq`) を導入
- `gcloud init` でプロジェクト紐付け、`gcloud auth application-default login` でADC認証
- Pythonは `uv` でプロジェクト管理。`.python-version=3.11` に固定
  - 理由: 後工程で使うProphet/InterpretML(EBM)/LightGBMとの互換性を考慮し、Python・pandasともに最新版を避けて枯れたバージョンを採用

### リポジトリ構成
pipeline/
etl/
to_bq.py # raw層: CSV→BigQueryロード
make_silver_table.py # silver層: 前処理SQLの実行
sql/
make_prep_data.sql # 前処理SQL本体
notebooks/
01_eda.ipynb # EDA専用（今後使用）

- `.py`と`.sql`をファイル分離（保守性のため）
- `notebooks/`はEDA専用、ETLコードは`pipeline/`配下に分離（ディレクトリ名から用途が推測できるように）
- `.gitignore`に`.venv/`を追加
### raw層（`raw_zone.osaka_pref`）
- 国交省の中古マンションデータ（大阪府、2014〜2025年、12ファイル・約76,658行）をpandasで読み込みBigQueryへロード
- **文字コード**: `cp932`を指定（`shift_jis`ではNEC拡張文字を含む一部データでデコードエラー）
- **dtype=str**で読み込み、生データの型・欠損をそのまま保全
- **カラム名**: 日本語ヘッダーを英語snake_caseにpandas側でリネーム（BigQueryは従量課金のため、SQL側で処理を増やさない判断）
- **サロゲートキー**: pandas側で`uuid.uuid4()`により`id`列を発行（部分的なファイル差し替え運用を想定し、キー衝突を避けるため）
- **書き込み**: `write_disposition=WRITE_TRUNCATE`で冪等性を担保（何度再実行しても同じ結果になる）
- レイヤー分離の理由: 前処理をやり直す際に生データへ戻れるようにするため
### silver層（`silver_zone.osaka_pref`）
`pipeline/sql/make_prep_data.sql`にて、`CREATE SCHEMA IF NOT EXISTS` + `CREATE OR REPLACE TABLE ... AS SELECT`で構築。
| カラム | 処理内容 |
|---|---|
| `transaction_price`, `coverage_ratio`, `floor_area_ratio` | 単純CAST(INT64) |
| `area_sqm` | CAST。"2,000㎡以上"はNULL化 + `area_no_max_limit_flag` |
| `building_year` | "年"以降を除去してCAST。"戦前"はNULL化 + `building_before_war_flag` |
| `time_to_station` | レンジ表記を分に変換して中央値採用（30分〜60分→45分など）。レンジ表記だったかを`time_range_write_flag`、上限なし("2H〜")を`time_no_max_limit_flag`で記録 |
| `transaction_period` | `transaction_year`, `transaction_quarter`に分解 |
| その他カラム | rawのままパススルー |
欠損値の扱い方針: 不確実な値を代理の数値で無理に埋めるより、**NULL＋フラグ**で情報を残す（EBMは欠損値をそのまま扱えるため、この方針と相性が良い）。
### つまずいたポイント（学び）
- BigQueryのCSVロードジョブは`Shift_JIS`/`cp932`のような文字コードを直接サポートしない → pandas経由でDataFrameとして読み込み、`load_table_from_dataframe`で回避
- `shift_jis`と`cp932`は別物。国交省データはcp932でないとデコードエラーになる箇所がある
- 波ダッシュ「〜」(U+301C)と全角チルダ「～」(U+FF5E)は見た目がほぼ同じだが別のUnicode文字。SQLで手打ちすると片方だけ実データと不一致になり、CASE文が静かに失敗する（比較にマッチせず、CASTエラーへ）
- `load_table_from_dataframe`には`pyarrow`が別途必要
- `LoadJobConfig`（ロードジョブ用）と`client.query()`（クエリジョブ用）は別物で、混同すると動かない
### 現状・次のステップ
raw層・silver層ともに構築完了。次はF-2（EDA・ドメイン特徴量エンジニアリング、Pythonフェーズ）へ。外部データ（インバウンド数、観光地ランキング、駅乗換辞書、都市開発フラグ）は未取得。

## BigQueryを活用したデータ処理

### 全体像
[12個のCSV(cp932)]
→ pandasで読み込み・結合・キー付与
→ BigQuery raw_zone.osaka_pref（生データ層）
→ SQLで型変換・欠損フラグ・レンジ表記の数値化
→ BigQuery silver_zone.osaka_pref（前処理済み層）

### raw_zone.osaka_pref（生データ層）
- 国交省の中古マンション取引データ（大阪府、2014〜2025年、12ファイル・約76,658行）を、加工せずそのままロードしたテーブル
- 全カラムSTRING型（`dtype=str`で読み込み、生データの型・欠損をそのまま保全）
- カラム名は日本語ヘッダーから英語snake_caseにリネーム済み
- 行ごとに一意な`id`（UUID）を付与。silver層との紐付け・前処理のやり直しに利用
- `WRITE_TRUNCATE`で洗い替え。何度実行しても同じ状態になる
### silver_zone.osaka_pref（前処理済み層）
`CREATE SCHEMA IF NOT EXISTS silver_zone` + `CREATE OR REPLACE TABLE ... AS SELECT`で、`raw_zone.osaka_pref`から生成。
| カラム | SQLでの処理内容 |
|---|---|
| `transaction_price`, `coverage_ratio`, `floor_area_ratio` | `CAST(... AS INT64)`で単純に数値型へ変換 |
| `area_sqm` | 数値へCAST。ただし"2,000㎡以上"（上限なし表記）は`NULLIF`でNULL化し、`area_no_max_limit_flag`で元の状態を記録 |
| `building_year` | "○○年"から年数部分を`SUBSTRING`で抽出しCAST。"戦前"はNULL化し、`building_before_war_flag`で記録 |
| `time_to_station` | "30分〜60分"のようなレンジ表記を`CASE`で分単位の中央値に変換（例: 30分〜60分→45分、1H〜1H30→75分、2H〜→135分）。レンジ表記だったかどうかを`time_range_write_flag`、上限なし("2H〜")かどうかを`time_no_max_limit_flag`として別途保持 |
| `transaction_period` | "2014年第2四半期"を`transaction_year`・`transaction_quarter`に分解（`SUBSTRING`で年部分・四半期数字を抽出） |
| 上記以外の全カラム | rawのまま変換なしでパススルー |
| `id` | 3つのCTE（数値CAST系・欠損処理系・パススルー系）を`id`でJOINし、1テーブルに統合するためのキーとして使用 |
**共通方針**: 曖昧・上限なしの値は、代理の数値で無理に埋めずに**NULL＋フラグ列**で情報を残す形に統一。





