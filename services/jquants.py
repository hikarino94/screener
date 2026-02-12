"""J-Quants API V2 クライアント

V2ではAPIキーを x-api-key ヘッダーに付与するだけで認証完了。
V1のメール/パスワードによるトークン認証フローは不要。
"""

import time
import logging
from datetime import date
from typing import Optional

import httpx
import pandas as pd

from config import config

logger = logging.getLogger(__name__)


class JQuantsClient:
    """J-Quants API V2 のHTTPクライアント

    認証:
    - x-api-key ヘッダーにAPIキーを付与するだけでOK
    """

    def __init__(self):
        self.base_url = config.jquants.base_url
        self.api_key = config.jquants.api_key
        self._client = httpx.Client(
            timeout=30.0,
            headers={"x-api-key": self.api_key},
        )

    def _get(self, endpoint: str, params: Optional[dict] = None) -> dict:
        """GETリクエスト（ページング対応）"""
        all_data = {}
        next_token = None

        while True:
            request_params = params.copy() if params else {}
            if next_token:
                request_params["pagination_key"] = next_token

            resp = self._client.get(
                f"{self.base_url}{endpoint}",
                params=request_params,
            )
            resp.raise_for_status()
            data = resp.json()

            # データをマージ
            for key, value in data.items():
                if key == "pagination_key":
                    continue
                if isinstance(value, list):
                    all_data.setdefault(key, []).extend(value)
                else:
                    all_data[key] = value

            # 次ページがあるか確認
            next_token = data.get("pagination_key")
            if not next_token:
                break

            # レートリミット対策
            time.sleep(0.5)

        return all_data

    # ─── 銘柄マスタ ───

    # ─── 銘柄マスタ ───

    def get_listed_stocks(self) -> pd.DataFrame:
        """上場銘柄一覧を取得"""
        data = self._get("/equities/master")
        items = data.get("equities_master") or data.get("data") or []
        return pd.DataFrame(items)

    # ─── 株価 ───

    # ─── 株価 ───

    def get_daily_prices(
        self,
        code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """株価四本値を取得"""
        params = {}
        if code:
            params["code"] = code
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/equities/bars/daily", params)
        items = data.get("equities_bars_daily") or data.get("data") or []
        df = pd.DataFrame(items)

        if not df.empty and "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])

        return df

    # ─── 財務情報 ───

    def get_financial_summary(
        self,
        code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """財務サマリを取得"""
        params = {}
        if code:
            params["code"] = code
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/fins/summary", params)
        items = data.get("fins_summary") or data.get("data") or []
        return pd.DataFrame(items)

    def get_financial_details(
        self,
        code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """財務諸表(BS/PL/CF)を取得"""
        params = {}
        if code:
            params["code"] = code
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/fins/details", params)
        items = data.get("fins_details") or data.get("data") or []
        return pd.DataFrame(items)

    # ─── 配当 ───

    def get_dividend(
        self,
        code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """配当金情報を取得"""
        params = {}
        if code:
            params["code"] = code
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/fins/dividend", params)
        items = data.get("fins_dividend") or data.get("data") or []
        return pd.DataFrame(items)

    # ─── 決算予定 ───

    def get_earnings_calendar(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """決算発表予定日を取得"""
        params = {}
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/equities/earnings-calendar", params)
        items = data.get("earnings_calendar") or data.get("data") or []
        return pd.DataFrame(items)

    # ─── 市場情報 ───

    def get_margin_interest(
        self,
        code: Optional[str] = None,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """信用取引週末残高を取得"""
        params = {}
        if code:
            params["code"] = code
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/markets/margin-interest", params)
        items = data.get("margin_interest") or data.get("data") or []
        return pd.DataFrame(items)

    def get_short_ratio(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """業種別空売り比率を取得"""
        params = {}
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/markets/short-ratio", params)
        items = data.get("short_ratio") or data.get("data") or []
        return pd.DataFrame(items)

    def get_trading_calendar(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """取引カレンダーを取得"""
        params = {}
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/markets/calendar", params)
        items = data.get("trading_calendar") or data.get("data") or []
        return pd.DataFrame(items)

    # ─── 指数 ───

    def get_index_prices(
        self,
        from_date: Optional[date] = None,
        to_date: Optional[date] = None,
    ) -> pd.DataFrame:
        """指数四本値を取得"""
        params = {}
        if from_date:
            params["from"] = from_date.strftime("%Y%m%d")
        if to_date:
            params["to"] = to_date.strftime("%Y%m%d")

        data = self._get("/indices/bars/daily", params)
        items = data.get("indices_bars_daily") or data.get("data") or []
        return pd.DataFrame(items)

    def close(self):
        """クライアントを閉じる"""
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
