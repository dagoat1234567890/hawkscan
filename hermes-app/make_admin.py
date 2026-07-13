import sqlite3

def make_admin():
    email = input("Enter the email address of the account you want to make an admin: ").strip().lower()
    
    conn = sqlite3.connect('users.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM users WHERE email = ?", (email,))
    user = cursor.fetchone()
    
    if user:
        cursor.execute("UPDATE users SET is_admin = 1 WHERE email = ?", (email,))
        conn.commit()
        print(f"Success! {email} is now an admin.")
        print("Please log out and log back in to activate your admin privileges.")
    else:
        print(f"Error: Could not find a user with the email {email}.")
        
    conn.close()

if __name__ == '__main__':
    make_admin()
