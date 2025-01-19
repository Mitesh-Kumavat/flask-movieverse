# database/create_user_table.py
import sqlite3

def create_users_table():
    conn = sqlite3.connect('database/movies.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            userId INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            watchlist TEXT DEFAULT '[]',
            favorites TEXT DEFAULT '[]'
        )
    ''')

    conn.commit()
    conn.close()
    print("Users table created successfully.")

if __name__ == "__main__":
    create_users_table()
