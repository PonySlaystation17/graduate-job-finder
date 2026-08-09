import sqlite3
from datetime import date

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

def save_job_to_db(job, database_name="jobs.db"):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    today = str(date.today())

    cursor.execute("""
        INSERT OR IGNORE INTO jobs
        (
            title,
            company,
            location,
            salary_min,
            salary_max,
            url,
            score,
            date_found,
            source,
            last_seen,
            active
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        job["title"],
        job["company"],
        job["location"],
        job.get("salary_min", 0),
        job.get("salary_max", 0),
        job["url"],
        job["score"],
        today,
        job["source"],
        today,
        1
    ))
    is_new_job = cursor.rowcount == 1

    cursor.execute("""
        UPDATE jobs
        SET
            last_seen = ?,
            active = 1,
            salary_min = ?,
            salary_max = ?,
            score = ?,
            url = ?,
            source = ?
        WHERE url = ?
        OR (
            title = ?
            AND company = ?
            AND location = ?
        )
    """, (
        today,
        job.get("salary_min", 0),
        job.get("salary_max", 0),
        job["score"],
        job["url"],
        job["source"],
        job["url"],
        job["title"],
        job["company"],
        job["location"]
    ))

    connection.commit()
    connection.close()

    return is_new_job

def mark_job_as_applied_by_url(job_url, database_name="jobs.db"):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE jobs
    SET applied = 1
    WHERE url = ?
    """, (job_url,))

    connection.commit()
    connection.close()

def mark_job_as_applied_by_url(job_url, database_name="jobs.db"):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute("""
    UPDATE jobs
    SET applied = 1
    WHERE url = ?
    """, (job_url,))

    connection.commit()
    connection.close()

def mark_stale_jobs_inactive(days_old=14, database_name = "jobs.db", source=None):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    if source is None:
        cursor.execute("""
            UPDATE jobs
            SET active = 0
            WHERE applied = 0
            AND last_seen < date('now', ?)
        """, (f"-{days_old} days",))
    else:
        cursor.execute("""
            UPDATE jobs
            SET active = 0
            WHERE applied = 0
            AND source = ?
            AND last_seen < date('now', ?)
        """, (
            source,
            f"-{days_old} days"
        ))

    connection.commit()
    connection.close()

def remove_job(job_url, database_name="jobs.db"):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute("""
        DELETE FROM jobs
        WHERE url = ?
    """, (job_url,))

    connection.commit()
    connection.close()

def get_top_jobs(limit=10, database_name="jobs.db"):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, company, location, score, salary_min, source
        FROM jobs
        WHERE applied = 0
        AND active = 1
        ORDER BY score DESC
        LIMIT ?
    """, (limit,))

    jobs = cursor.fetchall()
    connection.close()

    return jobs

def get_applied_jobs(database_name="jobs.db"):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, company, location, source
        FROM jobs
        WHERE applied = 1
        ORDER BY id DESC
    """)

    jobs = cursor.fetchall()
    connection.close()

    return jobs

def get_top_unapplied_jobs(limit=10, database_name="jobs.db"):
    connection = sqlite3.connect(database_name)
    cursor = connection.cursor()

    cursor.execute("""
        SELECT id, title, company, location, source, score
        FROM jobs
        WHERE applied = 0
        AND active = 1
        ORDER BY score DESC
        LIMIT ?
    """, (limit,))

    jobs = cursor.fetchall()
    connection.close()

    return jobs







