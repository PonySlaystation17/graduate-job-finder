import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import setup_database


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


if __name__ == "__main__":
    unittest.main()