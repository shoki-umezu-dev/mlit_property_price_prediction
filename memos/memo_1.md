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
判断	内容	理由
レイヤー分離	raw層(生データ)とsilver層(前処理済み)を分ける	前処理をやり直す際に生データから再スタートできるようにするため
取り込み方式	CSVを直接BigQueryにロードせず、pandasで読み込んでDataFrameとして送る	BigQueryのCSVロードジョブがcp932/Shift-JISのような文字コードを直接サポートしないため
文字コード	shift_jisではなくcp932を指定	国交省データにNEC拡張文字が含まれ、標準shift_jisではデコードエラーになったため
dtype	全列dtype=strで読み込み	raw層の「生データ保全」という目的に合わせ、pandas/BigQueryの自動型推定に委ねない
カラム名	日本語ヘッダーを英語snake_caseにリネーム。pandas側で実施	コードは英語ベースが実務的。SQL側で行うと従量課金のBigQuery処理が1ステップ増えるため、pandas側で行うコスト判断
サロゲートキー	pandas側でuuid.uuid4()を発行しid列として付与	将来「特定年のファイルだけ差し替え」という部分差し替え運用を想定し、既存行とキーが衝突しないようにするため。当初BigQuery側のDEFAULT GENERATE_UUID()案も検討したが、同じ目的をより単純に実現できるpandas側の方式を採用
書き込み方式	write_disposition=WRITE_TRUNCATE	開発中に何度再実行しても同じ結果になる(冪等性)ようにするため
差し替え単位の判別	transaction_period列で年・四半期が分かるため、専用の「ソースファイル」列は不要と判断	既存カラムで十分に用途を満たせるため

4. 実装・実行
- pipeline/etl/to_bq.py を作成し、12個のCSV（2014〜2025年、Shift-JIS系）を読み込み→結合→リネーム→キー付与→BigQueryへロード
- 依存関係のトラブルシュート: pyarrowが必要（load_table_from_dataframeの要件）
- 実行成功: raw_zone.osaka_pref テーブルにデータ投入済みを確認済み（pandas-gbqの将来的な必須化に関するFutureWarningは残存、未対応）
5. 現在地と次のステップ
raw層の構築（F-1の「取り込み」部分）は完了。次は silver層への前処理SQL の設計に入るところです（pipeline/sql/配下に実装予定）。想定される変換対象は、価格・面積等の数値CAST、time_to_stationの"30分〜60分"表記の数値化、building_yearの和暦変換、transaction_periodの年/四半期分解、欠損フラグの付与などです。この部分の方針はまだ固まっていません。

以上が現時点までの流れです。続きは、次にどのカラムから前処理SQLに着手するか、というところからですね。


