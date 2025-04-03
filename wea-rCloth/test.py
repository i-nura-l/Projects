from db import get_connection

try:
    conn = get_connection()
    print("Connection successful!")
    conn.close()
except Exception as e:
    print("Connection error:", e)