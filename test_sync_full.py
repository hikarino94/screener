"""全銘柄データ同期テストスクリプト

1. 指定した1日（平日）の全銘柄株価を取得
2. 同日の全財務情報を取得
3. DBに格納されたか確認
"""
import sys
import logging
from pathlib import Path
from datetime import date, timedelta
import pandas as pd

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)

sys.path.insert(0, str(Path(__file__).parent))

try:
    from db.database import get_session
    from models.schemas import DailyPrice, FinancialSummary
    from services.sync import SyncService
except ImportError as e:
    print(f"Import Error: {e}")
    sys.exit(1)

def main():
    print("=== 全銘柄同期テスト開始 ===", flush=True)
    
    sync = SyncService()
    session = get_session()

    # テスト対象日: Freeプラン考慮（直近12週間は取得不可 -> 90日前）
    # さらに平日になるように調整
    target_date = date.today() - timedelta(days=90)
    while target_date.weekday() >= 5: # 土日なら遡る
        target_date -= timedelta(days=1)
    
    # 確実にデータがある日
    print(f"対象日: {target_date}", flush=True)

    # 1. 全銘柄株価同期
    try:
        sync.sync_daily_prices_on_date(target_date)
        
        # 件数確認
        count = session.query(DailyPrice).filter(DailyPrice.date == target_date).count()
        print(f"株価データ同期成功: {count} 件 (期待値: 4000件以上)", flush=True)
        
        # サンプル確認
        sample = session.query(DailyPrice).filter(DailyPrice.date == target_date).first()
        if sample:
            print(f"サンプル: {sample.code} Close={sample.close} Vol={sample.volume}", flush=True)
            
    except Exception as e:
        print(f"株価同期エラー: {e}", flush=True)

    # 2. 全財務情報同期
    # 財務情報は毎日出るわけではないので、件数は少ない（0〜数百件）
    # 決算発表シーズンでないと0件もあり得る
    try:
        sync.sync_financial_summary_on_date(target_date)
        
        count_fin = session.query(FinancialSummary).filter(FinancialSummary.disclosed_date == target_date).count()
        print(f"財務データ同期成功: {count_fin} 件", flush=True)
        
    except Exception as e:
        print(f"財務同期エラー: {e}", flush=True)

    # 3. 複数期間（履歴）同期テスト
    # 負荷を考慮して2日間だけテスト
    print("\n=== 複数期間（履歴）同期テスト開始 ===", flush=True)
    from_date = target_date - timedelta(days=1)
    to_date = target_date
    
    # 土日またぎテストをしたいが、シンプルに平日2日間
    while from_date.weekday() >= 5:
        from_date -= timedelta(days=1)
        to_date -= timedelta(days=1)
        
    print(f"期間: {from_date} ~ {to_date}", flush=True)
    
    try:
        sync.sync_all_historical_data(from_date, to_date)
        
        # 件数確認
        count_days = session.query(DailyPrice.date).filter(
            DailyPrice.date >= from_date, 
            DailyPrice.date <= to_date
        ).distinct().count()
        
        print(f"履歴同期完了: {count_days} 日分のデータを確認 (期待値: 2日)", flush=True)
        
    except Exception as e:
        print(f"履歴同期エラー: {e}", flush=True)

    session.close()
    print("=== テスト完了 ===", flush=True)

if __name__ == "__main__":
    main()
