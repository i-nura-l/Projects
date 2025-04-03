import os
import psycopg2

def get_connection():
    try:
        conn = psycopg2.connect(
            host=os.getenv("DB_HOST", "localhost"),
            dbname=os.getenv("DB_NAME", "wea_rcloth"),
            user=os.getenv("DB_USER", "postgres"),
            password=os.getenv("DB_PASSWORD", "your_password_here")  # Replace with your actual password
        )
        return conn
    except Exception as e:
        print("Error connecting to PostgreSQL:", e)
        raise
