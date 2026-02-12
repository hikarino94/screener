# Screener - 投資補助ツール

日本株投資を支援するスクリーニングツール。

## 機能

- **J-Quants API連携**: 株価・財務データ取得
- **TDnetスクレイピング**: 最新決算資料の取得
- **テクニカル分析**: 移動平均、MACD、RSI等
- **ファンダメンタル分析**: PER、PBR、ROE等
- **AI決算分析**: Geminiによる決算資料の要約・業績変貌銘柄の検出

## セットアップ

```bash
# 仮想環境の作成・有効化
python -m venv .venv
source .venv/bin/activate

# 依存パッケージのインストール
pip install -r requirements.txt

# 環境変数の設定
cp .env.example .env
# .env を編集してAPIキーを設定

# アプリの起動
streamlit run app.py
```

## ディレクトリ構成

```
screener/
├── app.py              # メインアプリ
├── config.py           # 設定管理
├── services/           # サービス層
│   ├── jquants.py      # J-Quants APIクライアント
│   ├── tdnet.py        # TDnetスクレイパー
│   ├── technical.py    # テクニカル分析
│   ├── fundamental.py  # ファンダメンタル分析
│   └── ai_analyzer.py  # AI決算分析
├── models/             # データモデル
├── db/                 # DB管理
├── data/               # ローカルデータ
└── tests/              # テスト
```