import bcrypt
from db import get_connection

def create_user(name, email, password):
    conn = get_connection()
    cur = conn.cursor()
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    try:
        cur.execute("INSERT INTO users (name, email, password) VALUES (%s, %s, %s)",
                    (name, email, hashed.decode()))
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        print("Error in create_user:", e)
        return False
    finally:
        cur.close()
        conn.close()

def login_user(email, password):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, name, email, password, role FROM users WHERE email=%s", (email,))
    user = cur.fetchone()
    cur.close()
    conn.close()
    if user and bcrypt.checkpw(password.encode(), user[3].encode()):
        return {'id': user[0], 'name': user[1], 'email': user[2], 'role': user[4]}
    return None
