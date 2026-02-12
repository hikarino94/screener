"""アプリケーション設定管理"""

import os
from dataclasses import dataclass, field
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# ベースディレクトリ
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
PDF_DIR = DATA_DIR / "pdfs"
CACHE_DIR = DATA_DIR / "cache"
DB_PATH = DATA_DIR / "screener.db"

# ディレクトリの自動作成
for d in [DATA_DIR, PDF_DIR, CACHE_DIR]:
    d.mkdir(parents=True, exist_ok=True)


@dataclass
class JQuantsConfig:
    """J-Quants API V2 設定"""

    api_key: str = field(default_factory=lambda: os.getenv("JQUANTS_API_KEY", ""))
    plan: str = field(default_factory=lambda: os.getenv("JQUANTS_PLAN", "free"))
    base_url: str = "https://api.jquants.com/v2"

    @property
    def is_free_plan(self) -> bool:
        return self.plan == "free"


@dataclass
class GeminiConfig:
    """Gemini API設定"""

    api_key: str = field(default_factory=lambda: os.getenv("GEMINI_API_KEY", ""))
    model: str = "gemini-2.0-flash"  # コスト最適


@dataclass
class AppConfig:
    """アプリケーション全体設定"""

    jquants: JQuantsConfig = field(default_factory=JQuantsConfig)
    gemini: GeminiConfig = field(default_factory=GeminiConfig)
    db_url: str = field(default_factory=lambda: f"sqlite:///{DB_PATH}")


config = AppConfig()
