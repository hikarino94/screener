"""データ同期サービス

J-Quants APIからデータを取得し、DBに保存する処理をまとめたモジュール。
"""

import logging
from datetime import date, datetime
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

    def sync_daily_prices(self, code: str, from_date: date, to_date: date):
        """日足株価の同期"""
        logger.info(f"株価同期開始: {code} ({from_date} ~ {to_date})")
        df = self.client.get_daily_prices(code=code, from_date=from_date, to_date=to_date)
        if df.empty:
            logger.warning(f"株価データなし: {code}")
            return
        
        # logger.info(f"Columns: {df.columns.tolist()}")
        # logger.info(f"Head: {df.head(1).to_dict(orient='records')}")

        session = get_session()
        try:
            for _, row in df.iterrows():
                # NaNをNoneに変換
                row = row.where(pd.notnull(row), None)
                
                stmt = insert(DailyPrice).values(
                    code=row["Code"],
                    date=row["Date"].date(),
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
                    },
                )
                session.execute(stmt)
            
            session.commit()
            logger.info(f"株価同期完了: {len(df)}件")
        except Exception as e:
            session.rollback()
            logger.error(f"株価同期エラー: {e}")
            raise
        finally:
            session.close()

    def sync_financial_summary(self, code: str, from_date: date, to_date: date):
        """財務サマリの同期"""
        logger.info(f"財務サマリ同期開始: {code}")
        df = self.client.get_financial_summary(code=code, from_date=from_date, to_date=to_date)
        if df.empty:
            logger.warning(f"財務データなし: {code}")
            return

        session = get_session()
        try:
            for _, row in df.iterrows():
                # 空文字・NaN処理のために行を辞書として扱う方が簡単かもしれない
                # しかしpandasのSeriesなのでそのままアクセス
                
                # Date型変換
                disclosed_date = self._safe_date(row.get("DiscDate"))
                
                # 四半期情報の取得 (CurPerType: '1Q', '2Q', '3Q', 'FY' etc.)
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
                    fiscal_year=row.get("CurFYSt")[0:4] if row.get("CurFYSt") else None, # YYYY-MM-DD -> YYYY
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
            logger.info(f"財務サマリ同期完了: {len(df)}件")
        except Exception as e:
            session.rollback()
            logger.error(f"財務サマリ同期エラー: {e}")
            raise
        finally:
            session.close()
