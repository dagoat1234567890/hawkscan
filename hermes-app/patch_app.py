import os

def patch_app():
    with open('app.py', 'r') as f:
        content = f.read()
        
    # Patch 1: token logic in api_analyze
    old_token_logic = """        if tokens_used > 0:
            cursor.execute("UPDATE users SET total_tokens_used = total_tokens_used + ? WHERE id = ?", (tokens_used, user_id))
            
        conn.commit()
        conn.close()
        
    return jsonify(results)"""
    new_token_logic = """        conn.commit()
        conn.close()
        
    if tokens_used > 0:
        conn = sqlite3.connect(DATABASE)
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET total_tokens_used = total_tokens_used + ? WHERE id = ?", (tokens_used, user_id))
        conn.commit()
        conn.close()
        
    return jsonify(results)"""
    
    # Patch 2: Error logging in background_scan
    old_bg_error = """            tokens_used = results.get('tokens_used', 0)
            
            def safe_float(v):"""
    new_bg_error = """            tokens_used = results.get('tokens_used', 0)
            
            if results.get('error'):
                error_msg = results.get('message', 'Unknown error from agent')
                cursor.execute("INSERT INTO error_logs (user_id, error_message, endpoint) VALUES (?, ?, ?)", (user_id, error_msg, "background_scan"))
            
            def safe_float(v):"""
            
    # Patch 3: Ignore functional errors in price
    old_bg_price = """            my_price_raw = results.get("my_price")
            my_price = safe_float(my_price_raw) if my_price_raw != "Not Found" else None"""
    new_bg_price = """            my_price_raw = results.get("my_price")
            my_price = safe_float(my_price_raw) if my_price_raw != "Not Found" and my_price_raw != "Error" else None"""

    content = content.replace(old_token_logic, new_token_logic)
    content = content.replace(old_bg_error, new_bg_error)
    content = content.replace(old_bg_price, new_bg_price)
    
    with open('app.py', 'w') as f:
        f.write(content)
        
    print("app.py successfully patched!")

if __name__ == "__main__":
    patch_app()
