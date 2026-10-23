from db_connection import get_connection
import mysql.connector

def setup():
    # 1. Connect without specifying the database first
    con = get_connection(use_database=False)
    cursor = con.cursor()

    # 2. Create the database (if it doesn't exist) and select it
    DB_NAME = "defaultdb" # Or read this from your environment variables
    cursor.execute(f"CREATE DATABASE IF NOT EXISTS {DB_NAME}")
    cursor.execute(f"USE {DB_NAME}")

    # 3. Create tables
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products(
            id INT PRIMARY KEY,
            name VARCHAR(50) NOT NULL,
            category VARCHAR(50) NOT NULL DEFAULT 'General',
            price INT NOT NULL,
            stock INT NOT NULL DEFAULT 0
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sales(
            sale_id INT AUTO_INCREMENT PRIMARY KEY,
            billno INT NOT NULL,
            pid INT NOT NULL,
            name VARCHAR(50) NOT NULL,
            category VARCHAR(50) NOT NULL DEFAULT 'General',
            qty INT NOT NULL,
            amount INT NOT NULL,
            sale_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (pid) REFERENCES products(id)
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users(
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(50) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL
        )
    """)

    con.commit()
    con.close()
    print("Database Ready inside target database!")

if __name__ == "__main__":
    setup()