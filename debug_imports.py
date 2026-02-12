"""インポートデバッグスクリプト"""
import sys
import os

print("=== START DEBUG ===", flush=True)

try:
    import httpx
    print("httpx OK", flush=True)
except ImportError:
    print("httpx NG", flush=True)

try:
    import pandas
    print("pandas OK", flush=True)
except ImportError:
    print("pandas NG", flush=True)

try:
    import sqlalchemy
    print("sqlalchemy OK", flush=True)
except ImportError:
    print("sqlalchemy NG", flush=True)

try:
    import sqlite3
    print("sqlite3 OK", flush=True)
except ImportError:
    print("sqlite3 NG", flush=True)

print("=== END DEBUG ===", flush=True)
