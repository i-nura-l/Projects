import os
import psycopg2

def get_connection():
    """
    Establishes and returns a connection to the PostgreSQL database.
    You can configure your connection parameters here or via environment variables.
    """
    conn = psycopg2.connect(
        host=os.getenv("DB_HOST", "localhost"),
        dbname=os.getenv("DB_NAME", "wea_rcloth"),
        user=os.getenv("DB_USER", "postgres"),
        password=os.getenv("DB_PASSWORD", "nura3578")  # Replace with your actual password
    )
    return conn
