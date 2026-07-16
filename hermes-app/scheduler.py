import sqlite3
import time
from datetime import datetime
from dotenv import load_dotenv
load_dotenv()
from emailer import send_price_drop_email
from hermes import HawkscanAgent

DATABASE = "users.db"

def run_analysis_job():
    print("Running 24/7 Analysis Job...")
    conn = sqlite3.connect(DATABASE)
    cursor = conn.cursor()
    
    current_hour = datetime.utcnow().hour
    
    # Determine which tiers to scan based on the current hour (UTC)
    # Pro: only at 00:00 UTC
    # Ultra: at 00:00, 08:00, 16:00 UTC
    allowed_tiers = []
    if current_hour == 0:
        allowed_tiers = ['pro', 'ultra']
    elif current_hour in [8, 16]:
        allowed_tiers = ['ultra']
        
    if not allowed_tiers:
        print(f"Hour {current_hour} UTC is not a scheduled scan time for any tier. Skipping.")
        conn.close()
        return

    placeholders = ','.join(['?'] * len(allowed_tiers))
    
    # Fetch all tracked products along with user emails
    query = f"""
        SELECT t.id, t.user_id, t.product_name, t.company_name, t.platform, 
               t.baseline_price, t.last_price, u.email, t.catalog_url 
        FROM trackers t
        JOIN users u ON t.user_id = u.id
        WHERE t.is_active = 1 AND u.plan_tier IN ({placeholders})
    """
    cursor.execute(query, allowed_tiers)
    trackers = cursor.fetchall()
    
    if not trackers:
        print("No products to track for the current scheduled tiers.")
        conn.close()
        return

    agent = HawkscanAgent()
    
    for tracker in trackers:
        t_id, user_id, product_name, company_name, platform, baseline_price, last_price, user_email, catalog_url = tracker
        
        print(f"Checking {product_name} on {platform} for {user_email}...")
        
        # Avoid rapid API calls
        time.sleep(2)
        
        try:
            cursor.execute("SELECT target_competitors FROM users WHERE id = ?", (user_id,))
            comp_row = cursor.fetchone()
            target_competitors = comp_row[0] if comp_row and comp_row[0] else None
            
            results = agent.analyze_prices(product_name, company_name, platform, catalog_url=catalog_url, target_competitors=target_competitors)
            
            if "my_price" in results and isinstance(results["my_price"], (int, float)):
                my_price = float(results["my_price"])
                
                # Update baseline_price with the live detected my_price
                cursor.execute("UPDATE trackers SET baseline_price = ? WHERE id = ?", (my_price, t_id))
                conn.commit()
                baseline_price = my_price
            else:
                print(f"Could not extract my_price for {product_name}, using last known baseline.")
            
            if "stats" in results and results["stats"]["min"] is not None:
                min_competitor_price = float(results["stats"]["min"])
                
                # Check for price drop compared to baseline (which is now live my_price)
                if baseline_price is not None and min_competitor_price < baseline_price:
                    # Only notify if it dropped further or we haven't notified about this price recently
                    if last_price is None or min_competitor_price < last_price:
                        print(f"Price drop detected! {min_competitor_price} < {baseline_price}")
                        
                        # Find the URL and seller for the cheapest competitor
                        cheapest_url = "N/A"
                        cheapest_seller = "A competitor"
                        if "competitors" in results:
                            for comp in results["competitors"]:
                                if float(comp.get("price", 0)) == min_competitor_price:
                                    cheapest_url = comp.get("url", "N/A")
                                    cheapest_seller = comp.get("seller", "A competitor")
                                    break
                                    
                        # Send Email
                        send_price_drop_email(
                            user_email, 
                            product_name, 
                            baseline_price, 
                            min_competitor_price, 
                            platform, 
                            cheapest_url,
                            cheapest_seller
                        )
                        
                        # Update last_price in DB
                        cursor.execute("UPDATE trackers SET last_price = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?", (min_competitor_price, t_id))
                        conn.commit()
            else:
                print(f"Could not extract min price for {product_name}")
        except Exception as e:
            print(f"Error analyzing {product_name}: {e}")
            
    conn.close()
    print("Finished Analysis Job.")

if __name__ == "__main__":
    from apscheduler.schedulers.blocking import BlockingScheduler
    scheduler = BlockingScheduler()
    # Run at the top of every hour
    scheduler.add_job(func=run_analysis_job, trigger="cron", minute=0)
    print("Starting background scheduler worker (BlockingScheduler)...")
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
