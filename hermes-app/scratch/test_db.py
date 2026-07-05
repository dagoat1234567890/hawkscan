import sqlite3
import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app")

conn = sqlite3.connect(r"C:\Users\Shagy\Documents\hermes-app\users.db")
cursor = conn.cursor()
cursor.execute("SELECT * FROM trackers")
rows = cursor.fetchall()
print("Tracked products:")
for row in rows:
    print(row)
    
cursor.execute("SELECT * FROM users")
users = cursor.fetchall()
print("\nUsers:")
for u in users:
    print(u)
    
conn.close()
