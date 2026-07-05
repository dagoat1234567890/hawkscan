import sqlite3
conn=sqlite3.connect('users.db')
print(conn.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='trackers'").fetchone()[0])
