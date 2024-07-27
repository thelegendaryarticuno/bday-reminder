# test_connection.py
import mysql.connector
from config import DATABASE_CONFIG

try:
    conn = mysql.connector.connect(**DATABASE_CONFIG)
    if conn.is_connected():
        print("Connected to MySQL database")
    conn.close()
except mysql.connector.Error as err:
    print(f"Error: {err}")
