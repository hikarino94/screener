"""データ同期機能テストスクリプト v2

1. テーブルを再作成（スキーマ変更を反映）
2. 銘柄マスタの同期
3. 特定銘柄（例: 7203 トヨタ）の株価データ同期（Freeプラン対策で過去データ）
4. 同じく財務データ同期
5. DBからデータを読み出して表示
"""

import sys
import logging
from pathlib import Path
from datetime import date, timedelta

# ロギング設定 (INFOレベル)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    stream=sys.stdout
)
logger = logging.getLogger(__name__)

print("Start script...", flush=True)

sys.path.insert(0, str(Path(__file__).parent))

try:
    from db.database import engine, get_session, SessionLocal
    from models.schemas import Base, Stock, DailyPrice, FinancialSummary
    from services.sync import SyncService
    print("Modules imported successfully.", flush=True)
except ImportError as e:
    print(f"Import Error: {e}", flush=True)
    sys.exit(1)


def main():
    print("=== データ同期テスト開始 ===", flush=True)

    # ── Step 0: テーブル再作成 ──
    print("\n0. テーブル再作成中...", flush=True)
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("テーブル再作成完了", flush=True)

    sync = SyncService()
    session = get_session()
    print("Service & Session initialized.", flush=True)

    # ── Step 1: 銘柄マスタ同期 ──
    print("\n1. 銘柄マスタ同期中...", flush=True)
    try:
        sync.sync_stocks()
        count = session.query(Stock).count()
        print(f"銘柄マスタ同期完了: DB内件数 = {count} 件", flush=True)
    except Exception as e:
        print(f"銘柄マスタ同期エラー: {e}", flush=True)

    # トヨタを探す
    target_code = "72030"
    stock = session.query(Stock).filter(Stock.code == target_code).first()
    if stock:
        print(f"確認: {stock.code} {stock.company_name} ({stock.market_name})", flush=True)
    else:
        similar = session.query(Stock).filter(Stock.code.like("7203%")).first()
        if similar:
            target_code = similar.code
            print(f"類似コード発見: {target_code} {similar.company_name}", flush=True)
        else:
            print("トヨタが見つかりません。スキップ。", flush=True)
            target_code = None

    if not target_code:
        print("\n=== テスト完了（銘柄マスタのみ） ===", flush=True)
        session.close()
        return

    # ── Step 2: 株価データ同期 ──
    # Freeプランは直近12週間のデータにアクセスできない → 1年前のデータを使う
    to_date = date.today() - timedelta(days=365)
    from_date = to_date - timedelta(days=30)
    print(f"\n2. 株価データ同期中 (code={target_code}, {from_date} ~ {to_date})...", flush=True)
    try:
        sync.sync_daily_prices(target_code, from_date, to_date)
        prices = session.query(DailyPrice).filter(DailyPrice.code == target_code).all()
        print(f"株価データ同期完了: DB内件数 = {len(prices)} 件", flush=True)
        if prices:
            latest = prices[-1]
            print(f"最新データ: {latest.date} 終値 {latest.close}円", flush=True)
    except Exception as e:
        print(f"株価データ同期エラー: {e}", flush=True)

    # ── Step 3: 財務データ同期 ──
    to_date_fin = date.today() - timedelta(days=365)
    from_date_fin = to_date_fin - timedelta(days=365)
    print(f"\n3. 財務データ同期中 (code={target_code}, {from_date_fin} ~ {to_date_fin})...", flush=True)
    try:
        sync.sync_financial_summary(target_code, from_date_fin, to_date_fin)
        fins = session.query(FinancialSummary).filter(FinancialSummary.code == target_code).all()
        print(f"財務データ同期完了: DB内件数 = {len(fins)} 件", flush=True)
        if fins:
            latest_fin = fins[-1]
            print(f"最新データ: 開示日 {latest_fin.disclosed_date} 売上高 {latest_fin.net_sales}", flush=True)
    except Exception as e:
        print(f"財務データ同期エラー（想定内）: {e}", flush=True)
        print("※財務データのカラム名不一致の可能性。直上のログを確認。", flush=True)

    session.close()
    print("\n=== テスト完了 ===", flush=True)


if __name__ == "__main__":
    main()
