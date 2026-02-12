"""インポート検証スクリプト"""
import sys
import os

print("1. Start verification", flush=True)

try:
    import pandas as pd
    print("2. pandas imported", flush=True)
except ImportError as e:
    print(f"Error importing pandas: {e}", flush=True)

try:
    import sqlalchemy
    from sqlalchemy import create_engine
    print("3. sqlalchemy imported", flush=True)
except ImportError as e:
    print(f"Error importing sqlalchemy: {e}", flush=True)

try:
    import sqlite3
    print("4. sqlite3 imported", flush=True)
except ImportError as e:
    print(f"Error importing sqlite3: {e}", flush=True)

try:
    conn = sqlite3.connect(":memory:")
    print("5. sqlite3 memory connection ok", flush=True)
    conn.close()
except Exception as e:
    print(f"Error connecting to sqlite3: {e}", flush=True)

# プロジェクトモジュールのインポート
sys.path.insert(0, os.getcwd())

try:
    from db.database import get_session, engine
    print("6. db.database imported", flush=True)
except ImportError as e:
    print(f"Error importing db.database: {e}", flush=True)

try:
    from services.sync import SyncService
    print("7. services.sync imported", flush=True)
except ImportError as e:
    print(f"Error importing services.sync: {e}", flush=True)

print("8. Verification done", flush=True)
