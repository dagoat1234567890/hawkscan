import sqlite3
import sys
sys.path.append(r"C:\Users\Shagy\Documents\hermes-app")
from scheduler import run_analysis_job

DATABASE = r"C:\Users\Shagy\Documents\hermes-app\users.db"

def test_iphone():
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    # Check if iPhone already exists
    cursor.execute("SELECT id FROM trackers WHERE product_name = 'iPhone 15 128GB Black'")
    row = cursor.fetchone()
    if not row:
        # Insert iPhone 15 for user 1 (shivenmaan@gmail.com)
        cursor.execute("""
            INSERT INTO trackers (user_id, product_name, company_name, platform, baseline_price)
            VALUES (1, 'iPhone 15 128GB Black', 'Apple Official', 'Noon', 2800.0)
        """)
        conn.commit()
        print("Inserted iPhone 15 into trackers.")
    else:
        print("iPhone 15 already exists in trackers.")
        
    conn.close()
    
    # Run the analysis job
    print("Running analysis job...")
    run_analysis_job()

if __name__ == "__main__":
    test_iphone()
