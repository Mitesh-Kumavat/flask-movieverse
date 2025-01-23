import sqlite3

def clear_tables():
    try:
        conn = sqlite3.connect('database/movies.db')
        cursor = conn.cursor()

        cursor.execute("DELETE FROM watchlist")
        print("All data from the watchlist table has been deleted.")

        cursor.execute("DELETE FROM users")
        print("All data from the users table has been deleted.")

        conn.commit()
        conn.close()
        print("Database cleared successfully.")

    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    clear_tables()
