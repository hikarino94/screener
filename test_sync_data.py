"""データ同期機能テストスクリプト

1. 銘柄マスタの同期（先頭100件）
2. 特定銘柄（例: 7203 トヨタ）の株価データ同期
3. 同じく財務データ同期
4. DBからデータを読み出して表示
を確認する。
"""

import sys
from pathlib import Path
from datetime import date, timedelta
import pandas as pd
from sqlalchemy import select

# プロジェクトルートパスを追加
sys.path.insert(0, str(Path(__file__).parent))

from db.database import get_session
from models.schemas import Stock, DailyPrice, FinancialSummary
from services.sync import SyncService

def main():
    print("=== データ同期テスト開始 ===", flush=True)
    sync = SyncService()
    session = get_session()

    # 1. 銘柄マスタ同期
    print("\n1. 銘柄マスタ同期中...", flush=True)
    try:
        # 全件は多いのでAPIクライアント側で制限できないが、
        # sync_stocksは全件取得してしまう。
        # テストなのでそのまま実行（数秒〜十数秒）
        sync.sync_stocks()
        
        count = session.query(Stock).count()
        print(f"銘柄マスタ同期完了: DB内件数 = {count} 件", flush=True)
        
        # サンプル表示
        stock = session.query(Stock).filter(Stock.code == "7203").first()
        if stock:
            print(f"確認: {stock.code} {stock.company_name} ({stock.market_name})", flush=True)
    except Exception as e:
        print(f"銘柄マスタ同期エラー: {e}", flush=True)

    # ターゲット銘柄: トヨタ自動車 (7203)
    target_code = "72030" # J-Quants V2のコードは5桁
    # V2のAPIでは4桁コードだと取得できない場合があるため、マスタから確認推奨だが、
    # とりあえず5桁コード(末尾0)で試す。
    
    # マスタから検索してみる
    t_stock = session.query(Stock).filter(Stock.code.like("7203%")).first()
    if t_stock:
        target_code = t_stock.code
        print(f"\nターゲット銘柄: {target_code} {t_stock.company_name}", flush=True)
    
    # 2. 株価同期
    print("\n2. 株価データ同期中 (過去30日)...", flush=True)
    to_date = date.today()
    from_date = to_date - timedelta(days=30)
    
    try:
        sync.sync_daily_prices(target_code, from_date, to_date)
        
        prices = session.query(DailyPrice).filter(DailyPrice.code == target_code).all()
        print(f"株価データ同期完了: DB内件数 = {len(prices)} 件", flush=True)
        if prices:
            latest = prices[-1]
            print(f"最新データ: {latest.date} 終値 {latest.close}円", flush=True)
    except Exception as e:
        print(f"株価同期エラー: {e}", flush=True)

    # 3. 財務データ同期
    print("\n3. 財務データ同期中 (過去1年)...", flush=True)
    from_date_fin = to_date - timedelta(days=365)
    
    try:
        sync.sync_financial_summary(target_code, from_date_fin, to_date)
        
        fins = session.query(FinancialSummary).filter(FinancialSummary.code == target_code).all()
        print(f"財務データ同期完了: DB内件数 = {len(fins)} 件", flush=True)
        if fins:
            latest_fin = fins[-1]
            print(f"最新データ: 開示日 {latest_fin.disclosed_date} 売上高 {latest_fin.net_sales}百万円", flush=True)
    except Exception as e:
        print(f"財務同期エラー: {e}", flush=True)
        import traceback
        traceback.print_exc()

    session.close()
    print("\n=== テスト完了 ===", flush=True)

if __name__ == "__main__":
    main()
