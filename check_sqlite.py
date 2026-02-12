import sys
print("Start sqlite3 check", flush=True)
import sqlite3
print("sqlite3 imported", flush=True)
conn = sqlite3.connect(":memory:")
print("sqlite3 memory connection ok", flush=True)
