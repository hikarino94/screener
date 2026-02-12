"""データ同期サービス

J-Quants APIからデータを取得し、DBに保存する処理をまとめたモジュール。
"""

import logging
from datetime import date, datetime, timedelta
from typing import List, Optional

import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy.dialects.sqlite import insert

from db.database import get_session
from models.schemas import Stock, DailyPrice, FinancialSummary
from services.jquants import JQuantsClient

logger = logging.getLogger(__name__)


class SyncService:
    def __init__(self):
        self.client = JQuantsClient()

    def _safe_float(self, value):
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _safe_date(self, value):
        if value is None or value == "":
            return None
        return pd.to_datetime(value).date()

    def sync_stocks(self):
        """銘柄マスタの同期"""
        logger.info("銘柄マスタ同期開始")
        df = self.client.get_listed_stocks()
        if df.empty:
            logger.warning("銘柄データが取得できませんでした")
            return

        session = get_session()
        try:
            # バルクインサート（SQLiteのupsert構文を使用）
            for _, row in df.iterrows():
                stmt = insert(Stock).values(
                    code=row["Code"],
                    company_name=row["CoName"],
                    company_name_english=row.get("CoNameEn"),
                    sector17_code=row.get("S17"),
                    sector17_name=row.get("S17Nm"),
                    sector33_code=row.get("S33"),
                    sector33_name=row.get("S33Nm"),
                    market_code=row.get("Mkt"),
                    market_name=row.get("MktNm"),
                    margin_code=row.get("Mrgn"),
                    updated_at=datetime.utcnow(),
                )
                # コンフリクト時は更新
                stmt = stmt.on_conflict_do_update(
                    index_elements=["code"],
                    set_={
                        "company_name": stmt.excluded.company_name,
                        "updated_at": datetime.utcnow(),
                    },
                )
                session.execute(stmt)
            
            session.commit()
            logger.info(f"銘柄マスタ同期完了: {len(df)}件")
        except Exception as e:
            session.rollback()
            logger.error(f"銘柄マスタ同期エラー: {e}")
            raise
        finally:
            session.close()

    def _save_daily_prices(self, df: pd.DataFrame):
        """株価データのDB保存（共通処理）"""
        if df.empty:
            return

        session = get_session()
        try:
            for _, row in df.iterrows():
                # NaNをNoneに変換
                row = row.where(pd.notnull(row), None)
                
                date_val = row["Date"]
                if hasattr(date_val, "date"):
                    date_val = date_val.date()

                stmt = insert(DailyPrice).values(
                    code=row["Code"],
                    date=date_val,
                    open=row["O"],
                    high=row["H"],
                    low=row["L"],
                    close=row["C"],
                    volume=row["Vo"],
                    turnover_value=row["Va"],
                    adjustment_factor=row["AdjFactor"],
                    adjustment_open=row["AdjO"],
                    adjustment_high=row["AdjH"],
                    adjustment_low=row["AdjL"],
                    adjustment_close=row["AdjC"],
                    adjustment_volume=row["AdjVo"],
                )
                stmt = stmt.on_conflict_do_update(
                    index_elements=["code", "date"],
                    set_={
                        "close": stmt.excluded.close,
                        "volume": stmt.excluded.volume,
                        # 必要に応じて更新項目を追加
                        "adjustment_close": stmt.excluded.adjustment_close,
                        "adjustment_factor": stmt.excluded.adjustment_factor,
                    },
                )
                session.execute(stmt)
            
            session.commit()
            logger.info(f"株価保存完了: {len(df)}件")
        except Exception as e:
            session.rollback()
            logger.error(f"株価保存エラー: {e}")
            raise
        finally:
            session.close()

    def sync_daily_prices(self, code: str, from_date: date, to_date: date):
        """日足株価の同期（個別銘柄・期間指定）"""
        logger.info(f"株価同期開始: {code} ({from_date} ~ {to_date})")
        df = self.client.get_daily_prices(code=code, from_date=from_date, to_date=to_date)
        if df.empty:
            logger.warning(f"株価データなし: {code}")
            return
        self._save_daily_prices(df)

    def sync_daily_prices_on_date(self, target_date: date):
        """日足株価の同期（全銘柄・日付指定）"""
        logger.info(f"全銘柄株価同期開始: {target_date}")
        df = self.client.get_daily_prices(date=target_date) # code指定なし
        if df.empty:
            logger.warning(f"株価データなし: {target_date}")
            return
        logger.info(f"取得件数: {len(df)}件 (at {target_date})")
        self._save_daily_prices(df)

    def _save_financial_summary(self, df: pd.DataFrame):
        """財務サマリのDB保存（共通処理）"""
        if df.empty:
            return

        session = get_session()
        try:
            for _, row in df.iterrows():
                # Date型変換
                disclosed_date = self._safe_date(row.get("DiscDate"))
                
                # 四半期情報の取得
                quarter = None
                per_type = str(row.get("CurPerType", ""))
                if "1Q" in per_type: quarter = 1
                elif "2Q" in per_type: quarter = 2
                elif "3Q" in per_type: quarter = 3
                elif "4Q" in per_type: quarter = 4

                stmt = insert(FinancialSummary).values(
                    code=row.get("Code"),
                    disclosed_date=disclosed_date,
                    disclosed_time=row.get("DiscTime"),
                    type_of_document=row.get("DocType"),
                    fiscal_year=row.get("CurFYSt")[0:4] if row.get("CurFYSt") else None,
                    fiscal_quarter=quarter,
                    
                    net_sales=self._safe_float(row.get("Sales")),
                    operating_profit=self._safe_float(row.get("OP")),
                    ordinary_profit=self._safe_float(row.get("OdP")),
                    profit=self._safe_float(row.get("NP")),
                    earnings_per_share=self._safe_float(row.get("EPS")),
                    
                    forecast_net_sales=self._safe_float(row.get("FSales")),
                    forecast_operating_profit=self._safe_float(row.get("FOP")),
                    forecast_ordinary_profit=self._safe_float(row.get("FOdP")),
                    forecast_profit=self._safe_float(row.get("FNP")),
                    forecast_earnings_per_share=self._safe_float(row.get("FEPS")),
                    
                    total_assets=self._safe_float(row.get("TA")),
                    equity=self._safe_float(row.get("Eq")),
                    equity_to_asset_ratio=self._safe_float(row.get("EqAR")),
                    book_value_per_share=self._safe_float(row.get("BPS")),
                    cash_flows_from_operating=self._safe_float(row.get("CFO")),
                    cash_flows_from_investing=self._safe_float(row.get("CFI")),
                    cash_flows_from_financing=self._safe_float(row.get("CFF")),
                    
                    result_dividend_per_share_annual=self._safe_float(row.get("DivTotalAnn")),
                    forecast_dividend_per_share_annual=self._safe_float(row.get("FDivTotalAnn")),
                    
                    updated_at=datetime.utcnow(),
                )
                # 財務データはユニーク制約がないため単発追加
                session.execute(stmt)

            session.commit()
            logger.info(f"財務サマリ保存完了: {len(df)}件")
        except Exception as e:
            session.rollback()
            logger.error(f"財務サマリ保存エラー: {e}")
            raise
        finally:
            session.close()

    def sync_financial_summary(self, code: str, from_date: date, to_date: date):
        """財務サマリの同期（個別銘柄・期間指定）"""
        logger.info(f"財務サマリ同期開始: {code}")
        df = self.client.get_financial_summary(code=code, from_date=from_date, to_date=to_date)
        if df.empty:
            logger.warning(f"財務データなし: {code}")
            return
        self._save_financial_summary(df)

    def sync_financial_summary_on_date(self, target_date: date):
        """財務サマリの同期（全銘柄・日付指定）"""
        logger.info(f"全銘柄財務サマリ同期開始: {target_date}")
        df = self.client.get_financial_summary(date=target_date) # code指定なし
        if df.empty:
            logger.warning(f"財務データなし: {target_date}")
            return
        logger.info(f"取得件数: {len(df)}件 (at {target_date})")
        self._save_financial_summary(df)

    def sync_all_historical_data(self, from_date: date, to_date: date):
        """指定期間の全銘柄データを同期（日付ループ）"""
        logger.info(f"過去全データ同期開始: {from_date} ~ {to_date}")
        
        current = from_date
        while current <= to_date:
            # 土日はスキップしてもいいが、APIが空を返すだけなのでそのまま呼ぶ
            # ただし無駄なリクエストを避けるなら平日チェックを入れる
            if current.weekday() < 5: # 月(0)〜金(4)
                logger.info(f"--- Processing {current} ---")
                try:
                    self.sync_daily_prices_on_date(current)
                    self.sync_financial_summary_on_date(current)
                except Exception as e:
                    logger.error(f"Error on {current}: {e}")
                    # 個別の日付のエラーで全体を止めない
            else:
                logger.debug(f"Skipping weekend: {current}")

            current += timedelta(days=1)
        
        logger.info("過去全データ同期完了")
