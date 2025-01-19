import sqlite3

conn = sqlite3.connect('database/movies.db')

conn.execute("DROP TABLE users")

conn.execute("""
CREATE TABLE IF NOT EXISTS users (
    userId INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password TEXT NOT NULL
);
""")

conn.execute("""
CREATE TABLE IF NOT EXISTS watchlist (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    userId INTEGER NOT NULL,
    movieName TEXT NOT NULL,
    movieImdbId TEXT NOT NULL,
    movieImg TEXT NOT NULL,
    UNIQUE(userId, movieImdbId),
    FOREIGN KEY (userId) REFERENCES users(userId) ON DELETE CASCADE
);
""")

conn.close()
print("Database initialized.")
   