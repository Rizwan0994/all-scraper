import mysql.connector
from mysql.connector import Error

try:
    connection = mysql.connector.connect(
        host="cp.miplimited.com",
        user="scrapping",
        password="el6xBRHruZ5BWqGhgvGA",
        database="scrapping",
        port=3306
    )

    if connection.is_connected():
        print("✅ Connected to MySQL database")
        cursor = connection.cursor()
        cursor.execute("SELECT NOW();")
        result = cursor.fetchone()
        print("Current DB Time:", result[0])

except Error as e:
    print("❌ Error while connecting to MySQL:", e)

finally:
    if 'connection' in locals() and connection.is_connected():
        connection.close()
        print("🔌 MySQL connection closed")
