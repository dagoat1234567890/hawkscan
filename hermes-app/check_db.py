import sqlite3
import os

dbs = ['users.db', 'app.db', 'hawkscan.db']
for db in dbs:
    if os.path.exists(db):
        try:
            conn = sqlite3.connect(db)
            tables = [x[0] for x in conn.execute('SELECT name FROM sqlite_master WHERE type="table"').fetchall()]
            if 'users' in tables:
                emails = [r[0] for r in conn.execute('SELECT email FROM users').fetchall()]
                print(f"{db}: {emails}")
            else:
                print(f"{db}: No users table")
            conn.close()
        except Exception as e:
            print(f"{db}: Error - {e}")
    else:
        print(f"{db}: File not found")
