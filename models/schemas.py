"""データモデル定義（SQLAlchemy ORM）"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    Boolean,
    Column,
    Date,
    DateTime,
    Float,
    Integer,
    String,
    Text,
    BigInteger,
    UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    """ベースモデル"""

    pass


class Stock(Base):
    """銘柄マスタ"""

    __tablename__ = "stocks"

    code = Column(String(10), primary_key=True)  # 銘柄コード
    company_name = Column(String(200))  # 会社名
    company_name_english = Column(String(200))  # 会社名（英語）
    sector17_code = Column(String(10))  # 17業種コード
    sector17_name = Column(String(100))  # 17業種名
    sector33_code = Column(String(10))  # 33業種コード
    sector33_name = Column(String(100))  # 33業種名
    market_code = Column(String(10))  # 市場区分コード
    market_name = Column(String(50))  # 市場区分名
    margin_code = Column(String(10))  # 信用区分
    fiscal_year_end = Column(String(10))  # 決算月
    is_active = Column(Boolean, default=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class DailyPrice(Base):
    """日足株価データ"""

    __tablename__ = "daily_prices"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True)  # 銘柄コード
    date = Column(Date, index=True)  # 日付
    open = Column(Float)  # 始値
    high = Column(Float)  # 高値
    low = Column(Float)  # 安値
    close = Column(Float)  # 終値
    volume = Column(BigInteger)  # 出来高
    turnover_value = Column(Float)  # 売買代金
    adjustment_factor = Column(Float)  # 調整係数
    adjustment_open = Column(Float)  # 調整済始値
    adjustment_high = Column(Float)  # 調整済高値
    adjustment_low = Column(Float)  # 調整済安値
    adjustment_close = Column(Float)  # 調整済終値
    adjustment_volume = Column(Float)  # 調整済出来高

    __table_args__ = (
        UniqueConstraint("code", "date", name="uix_code_date"),
    )


class FinancialSummary(Base):
    """財務サマリ"""

    __tablename__ = "financial_summaries"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True)
    disclosed_date = Column(Date)  # 開示日
    disclosed_time = Column(String(10))  # 開示時刻
    type_of_document = Column(String(50))  # 書類種別
    fiscal_year = Column(String(20))  # 会計年度
    fiscal_quarter = Column(Integer)  # 四半期

    # 売上・利益
    net_sales = Column(Float)  # 売上高
    operating_profit = Column(Float)  # 営業利益
    ordinary_profit = Column(Float)  # 経常利益
    profit = Column(Float)  # 当期純利益
    earnings_per_share = Column(Float)  # EPS

    # 予想
    forecast_net_sales = Column(Float)  # 売上高予想
    forecast_operating_profit = Column(Float)  # 営業利益予想
    forecast_ordinary_profit = Column(Float)  # 経常利益予想
    forecast_profit = Column(Float)  # 純利益予想
    forecast_earnings_per_share = Column(Float)  # EPS予想

    # その他
    total_assets = Column(Float)  # 総資産
    equity = Column(Float)  # 純資産
    equity_to_asset_ratio = Column(Float)  # 自己資本比率
    book_value_per_share = Column(Float)  # BPS
    cash_flows_from_operating = Column(Float)  # 営業CF
    cash_flows_from_investing = Column(Float)  # 投資CF
    cash_flows_from_financing = Column(Float)  # 財務CF

    result_dividend_per_share_annual = Column(Float)  # 年間配当（実績）
    forecast_dividend_per_share_annual = Column(Float)  # 年間配当（予想）

    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class EarningsReport(Base):
    """決算資料（TDnet）"""

    __tablename__ = "earnings_reports"

    id = Column(Integer, primary_key=True, autoincrement=True)
    code = Column(String(10), index=True)  # 銘柄コード
    company_name = Column(String(200))  # 会社名
    disclosed_date = Column(Date, index=True)  # 開示日
    title = Column(String(500))  # 資料タイトル
    document_url = Column(String(500))  # PDFのURL
    pdf_path = Column(String(500))  # ローカル保存パス
    extracted_text = Column(Text)  # 抽出テキスト

    # AI分析結果
    ai_summary = Column(Text)  # AI要約
    ai_keywords = Column(Text)  # 抽出キーワード (JSON)
    transformation_score = Column(Float)  # 業績変貌スコア (0-100)
    transformation_reasons = Column(Text)  # 変貌理由 (JSON)

    analyzed_at = Column(DateTime)  # 分析日時
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
