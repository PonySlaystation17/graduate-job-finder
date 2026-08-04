import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import setup_database, save_job_to_db


class TestDatabaseSetup(unittest.TestCase):

    def test_setup_database_creates_jobs_table(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("PRAGMA table_info(jobs)")
            columns = [column[1] for column in cursor.fetchall()]

            connection.close()

            self.assertIn("id", columns)
            self.assertIn("title", columns)
            self.assertIn("last_seen", columns)
            self.assertIn("active", columns)

    def test_save_job_to_db_inserts_job(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            job = {
                "title": "Graduate Software Engineer",
                "company": "Example Ltd",
                "location": "Liverpool",
                "salary_min": 30000,
                "salary_max": 35000,
                "url": "https://example.com/job/1",
                "score": 12,
                "source": "Test"
            }

            save_job_to_db(job, database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                SELECT title, company, applied, active
                FROM jobs
                WHERE url = ?
            """, (job["url"],))

            saved_job = cursor.fetchone()
            connection.close()

            self.assertEqual(
                saved_job,
                ("Graduate Software Engineer", "Example Ltd", 0, 1)
            )

if __name__ == "__main__":
    unittest.main()