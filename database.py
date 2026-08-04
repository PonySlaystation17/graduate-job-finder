import sqlite3

def setup_database(database_name="jobs.db"):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    # Create the table for a brand-new database.
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            company TEXT,
            location TEXT,
            salary_min INTEGER,
            salary_max INTEGER,
            url TEXT UNIQUE,
            score INTEGER,
            date_found TEXT,
            source TEXT,
            applied INTEGER DEFAULT 0,
            last_seen TEXT,
            active INTEGER DEFAULT 1,
            UNIQUE(title, company, location)
        )
    """)

    # Check which columns already exist in an older database.
    cursor.execute("PRAGMA table_info(jobs)")
    columns = [column[1] for column in cursor.fetchall()]

    # Add new columns only when they are missing.
    if "last_seen" not in columns:
        cursor.execute("""
            ALTER TABLE jobs
            ADD COLUMN last_seen TEXT
        """)

    if "active" not in columns:
        cursor.execute("""
            ALTER TABLE jobs
            ADD COLUMN active INTEGER DEFAULT 1
        """)

    # Fill the new fields for jobs already in the database.
    cursor.execute("""
        UPDATE jobs
        SET last_seen = date_found
        WHERE last_seen IS NULL
    """)

    cursor.execute("""
        UPDATE jobs
        SET active = 1
        WHERE active IS NULL
    """)

    connection.commit()
    connection.close()
