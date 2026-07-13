import sqlite3

def check():
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, email, is_admin, total_tokens_used FROM users")
    rows = cursor.fetchall()
    print("Users table:")
    for row in rows:
        print(f"ID: {row[0]}, Email: {row[1]}, Admin: {row[2]}, Tokens: {row[3]}")
    conn.close()

if __name__ == '__main__':
    check()
