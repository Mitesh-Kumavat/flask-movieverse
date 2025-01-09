import sqlite3
import pandas as pd

def csv_to_sqlite(csv_file, db_file):
    # Load the CSV file into a pandas DataFrame
    print("Loading CSV file...")
    data = pd.read_csv(csv_file)

    # Connect to SQLite database (it will create the file if it doesn't exist)
    print("Connecting to SQLite database...")
    conn = sqlite3.connect(db_file)
    cursor = conn.cursor()

    # Create the table in SQLite
    print("Creating table in SQLite database...")
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS movies (
            imdb_title_id TEXT PRIMARY KEY,
            title TEXT,
            original_title TEXT,
            year INTEGER,
            date_published TEXT,
            genre TEXT,
            duration INTEGER,
            country TEXT,
            language_1 TEXT,
            language_2 TEXT,
            language_3 TEXT,
            director TEXT,
            writer TEXT,
            actors TEXT,
            actors_1 TEXT,
            actors_f2 TEXT,
            description TEXT,
            desc35 TEXT,
            avg_vote REAL,
            votes INTEGER,
            budget INTEGER,
            usa_gross_income INTEGER,
            worldwide_gross_income INTEGER,
            reviews_from_users INTEGER
        )
    ''')

    # Write the data into the SQLite database
    print("Inserting data into the SQLite database...")
    data.to_sql('movies', conn, if_exists='replace', index=False)

    # Commit changes and close the connection
    conn.commit()
    conn.close()
    print(f"Database created successfully: {db_file}")

if __name__ == "__main__":
    # Specify the input CSV file and output SQLite database file
    csv_file = "./movies.csv"  # Replace with the path to your CSV file
    db_file = "./movies.db"    # Output SQLite database file

    csv_to_sqlite(csv_file, db_file)
