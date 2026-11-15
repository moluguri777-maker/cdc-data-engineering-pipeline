
from config.database import get_db_connection

connection = None

try:
    connection = get_db_connection()

    print("MySQL connection successful!")

    cursor = connection.cursor()
    cursor.execute("SELECT DATABASE()")

    print("Connected database:", cursor.fetchone()[0])

    cursor.execute("SHOW TABLES")

    print("\nAvailable tables:")
    for table in cursor.fetchall():
        print(table[0])

    cursor.close()

except Exception as error:
    print("Database connection failed:", error)

finally:
    if connection and connection.is_connected():
        connection.close()
        print("\nDatabase connection closed.")
