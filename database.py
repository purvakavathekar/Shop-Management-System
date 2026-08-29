from db_connection import get_connection

def setup():
    con = get_connection(use_database=False)
    cursor = con.cursor()

    cursor.execute("CREATE DATABASE IF NOT EXISTS shopproject")
    cursor.execute("USE shopproject")

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

    con.commit()
    con.close()
    print("Database Ready with Category Support!")

if __name__ == "__main__":
    setup()