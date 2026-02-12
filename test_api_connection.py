"""J-Quants API V2 接続テストスクリプト

実際のAPIキーを使用してJ-Quants API V2に接続し、
銘柄一覧を取得できるか確認します。
"""

import sys
import os
from pathlib import Path
import pandas as pd

# プロジェクトルートパスを追加
sys.path.insert(0, str(Path(__file__).parent))

try:
    from config import config
    from services.jquants import JQuantsClient
except ImportError as e:
    print(f"エラー: モジュールのインポートに失敗しました。\n{e}", flush=True)
    sys.exit(1)

def main():
    print("=== J-Quants API V2 接続テスト ===", flush=True)
    
    # 1. APIキーの確認
    if not config.jquants.api_key:
        print("エラー: APIキーが設定されていません。", flush=True)
        print(".env ファイルに JQUANTS_API_KEY を設定してください。", flush=True)
        return

    print(f"APIキーを確認しました: {config.jquants.api_key[:4]}****", flush=True)
    print(f"プラン: {config.jquants.plan}", flush=True)
    print("-" * 30, flush=True)

    # 2. クライアントの初期化
    try:
        client = JQuantsClient()
        print("J-QuantsClient 初期化成功", flush=True)
    except Exception as e:
        print(f"J-QuantsClient 初期化失敗: {e}", flush=True)
        return

    # 3. 銘柄一覧の取得テスト
    print("銘柄一覧 (/equities/master) を取得中...", flush=True)
    try:
        df = client.get_listed_stocks()
        
        if df.empty:
            print("警告: データが空です。API接続は成功しましたが、データが返ってきませんでした。", flush=True)
        else:
            print("取得成功！", flush=True)
            print(f"取得件数: {len(df)} 件", flush=True)
            print("\n--- データサンプル (先頭5件) ---", flush=True)
            print(df.head().to_string(), flush=True)
            print("--------------------------------", flush=True)

    except Exception as e:
        print(f"APIリクエストエラー: {e}", flush=True)
        return

    print("\n=== テスト完了 ===", flush=True)

if __name__ == "__main__":
    main()
