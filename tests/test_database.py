import sqlite3
import tempfile
import unittest
from pathlib import Path

from database import (
    setup_database,
    save_job_to_db,
    mark_job_as_applied_by_url,
    mark_stale_jobs_inactive,
    remove_job,
    get_top_jobs,
    get_applied_jobs,
    get_top_unapplied_jobs
    )


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

    def test_save_job_to_db_updates_existing_job(self):
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

            job["salary_min"] = 32000
            job["salary_max"] = 38000
            job["score"] = 18

            save_job_to_db(job, database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                SELECT salary_min, salary_max, score, active
                FROM jobs
                WHERE url = ?
            """, (job["url"],))

            updated_job = cursor.fetchone()

            cursor.execute("SELECT COUNT(*) FROM jobs")
            job_count = cursor.fetchone()[0]

            connection.close()

            self.assertEqual(updated_job, (32000, 38000, 18, 1))
            self.assertEqual(job_count, 1)

    def test_mark_job_as_applied_by_url(self):
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
            mark_job_as_applied_by_url(job["url"], database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                SELECT applied
                FROM jobs
                WHERE url = ?
            """, (job["url"],))

            applied = cursor.fetchone()[0]
            connection.close()

            self.assertEqual(applied, 1)

    def test_mark_stale_jobs_inactive(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO jobs
                (
                    title,
                    company,
                    location,
                    url,
                    score,
                    date_found,
                    source,
                    applied,
                    last_seen,
                    active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Old Graduate Job",
                "Old Company",
                "Liverpool",
                "https://example.com/old",
                10,
                "2026-01-01",
                "Test",
                0,
                "2026-01-01",
                1
            ))

            cursor.execute("""
                INSERT INTO jobs
                (
                    title,
                    company,
                    location,
                    url,
                    score,
                    date_found,
                    source,
                    applied,
                    last_seen,
                    active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Recent Graduate Job",
                "Recent Company",
                "Liverpool",
                "https://example.com/recent",
                10,
                "2026-08-07",
                "Test",
                0,
                "2026-08-07",
                1
            ))

            connection.commit()
            connection.close()

            mark_stale_jobs_inactive(14, database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                SELECT active
                FROM jobs
                WHERE url = ?
            """, ("https://example.com/old",))
            old_job_active = cursor.fetchone()[0]

            cursor.execute("""
                SELECT active
                FROM jobs
                WHERE url = ?
            """, ("https://example.com/recent",))
            recent_job_active = cursor.fetchone()[0]

            connection.close()

            self.assertEqual(old_job_active, 0)
            self.assertEqual(recent_job_active, 1)

    def test_remove_job_deletes_job(self):
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
            remove_job(job["url"], database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                SELECT COUNT(*)
                FROM jobs
                WHERE url = ?
            """, (job["url"],))

            job_count = cursor.fetchone()[0]
            connection.close()

            self.assertEqual(job_count, 0)

    def test_get_top_jobs_returns_highest_scores_first(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            low_score_job = {
                "title": "Junior Developer",
                "company": "Company A",
                "location": "Liverpool",
                "salary_min": 30000,
                "salary_max": 35000,
                "url": "https://example.com/low",
                "score": 5,
                "source": "Test"
            }

            high_score_job = {
                "title": "Graduate Software Engineer",
                "company": "Company B",
                "location": "London",
                "salary_min": 35000,
                "salary_max": 40000,
                "url": "https://example.com/high",
                "score": 20,
                "source": "Test"
            }

            save_job_to_db(low_score_job, database_path)
            save_job_to_db(high_score_job, database_path)

            jobs = get_top_jobs(
                limit=10,
                database_name=database_path
            )

            self.assertEqual(jobs[0][1], "Graduate Software Engineer")
            self.assertEqual(jobs[1][1], "Junior Developer")

    def test_get_applied_jobs_returns_only_applied_jobs(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            applied_job = {
                "title": "Graduate Software Engineer",
                "company": "Company A",
                "location": "Liverpool",
                "salary_min": 30000,
                "salary_max": 35000,
                "url": "https://example.com/applied",
                "score": 15,
                "source": "Test"
            }

            unapplied_job = {
                "title": "Junior Developer",
                "company": "Company B",
                "location": "London",
                "salary_min": 32000,
                "salary_max": 36000,
                "url": "https://example.com/unapplied",
                "score": 10,
                "source": "Test"
            }

            save_job_to_db(applied_job, database_path)
            save_job_to_db(unapplied_job, database_path)

            mark_job_as_applied_by_url(
                applied_job["url"],
                database_path
            )

            jobs = get_applied_jobs(database_path)

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0][1], "Graduate Software Engineer")

    def test_get_top_unapplied_jobs_returns_highest_unapplied_first(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            applied_job = {
                "title": "Applied Graduate Developer",
                "company": "Company A",
                "location": "Liverpool",
                "salary_min": 30000,
                "salary_max": 35000,
                "url": "https://example.com/applied",
                "score": 50,
                "source": "Test"
            }

            high_unapplied_job = {
                "title": "Graduate Software Engineer",
                "company": "Company B",
                "location": "London",
                "salary_min": 35000,
                "salary_max": 40000,
                "url": "https://example.com/high",
                "score": 20,
                "source": "Test"
            }

            low_unapplied_job = {
                "title": "Junior Developer",
                "company": "Company C",
                "location": "Manchester",
                "salary_min": 30000,
                "salary_max": 35000,
                "url": "https://example.com/low",
                "score": 8,
                "source": "Test"
            }

            save_job_to_db(applied_job, database_path)
            save_job_to_db(high_unapplied_job, database_path)
            save_job_to_db(low_unapplied_job, database_path)

            mark_job_as_applied_by_url(
                applied_job["url"],
                database_path
            )

            jobs = get_top_unapplied_jobs(
                limit=10,
                database_name=database_path
            )

            self.assertEqual(len(jobs), 2)
            self.assertEqual(jobs[0][1], "Graduate Software Engineer")
            self.assertEqual(jobs[1][1], "Junior Developer")

    def test_get_top_unapplied_jobs_excludes_inactive_jobs(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            active_job = {
                "title": "Graduate Software Engineer",
                "company": "Company A",
                "location": "Liverpool",
                "salary_min": 30000,
                "salary_max": 35000,
                "url": "https://example.com/active",
                "score": 10,
                "source": "Test"
            }

            inactive_job = {
                "title": "Junior Developer",
                "company": "Company B",
                "location": "London",
                "salary_min": 35000,
                "salary_max": 40000,
                "url": "https://example.com/inactive",
                "score": 50,
                "source": "Test"
            }

            save_job_to_db(active_job, database_path)
            save_job_to_db(inactive_job, database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE jobs
                SET active = 0
                WHERE url = ?
            """, (inactive_job["url"],))

            connection.commit()
            connection.close()

            jobs = get_top_unapplied_jobs(
                limit=10,
                database_name=database_path
            )

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0][1], "Graduate Software Engineer")

    def test_get_top_jobs_excludes_inactive_jobs(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            active_job = {
                "title": "Graduate Software Engineer",
                "company": "Company A",
                "location": "Liverpool",
                "salary_min": 30000,
                "salary_max": 35000,
                "url": "https://example.com/active-top",
                "score": 10,
                "source": "Test"
            }

            inactive_job = {
                "title": "Junior Developer",
                "company": "Company B",
                "location": "London",
                "salary_min": 35000,
                "salary_max": 40000,
                "url": "https://example.com/inactive-top",
                "score": 50,
                "source": "Test"
            }

            save_job_to_db(active_job, database_path)
            save_job_to_db(inactive_job, database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                UPDATE jobs
                SET active = 0
                WHERE url = ?
            """, (inactive_job["url"],))

            connection.commit()
            connection.close()

            jobs = get_top_jobs(
                limit=10,
                database_name=database_path
            )

            self.assertEqual(len(jobs), 1)
            self.assertEqual(jobs[0][1], "Graduate Software Engineer")

    def test_mark_stale_jobs_inactive_can_target_one_source(self):
        with tempfile.TemporaryDirectory() as temp_directory:
            database_path = Path(temp_directory) / "test_jobs.db"

            setup_database(database_path)

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                INSERT INTO jobs
                (
                    title, company, location, url, score,
                    date_found, source, applied, last_seen, active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Old Adzuna Job",
                "Company A",
                "Liverpool",
                "https://example.com/adzuna-old",
                10,
                "2026-01-01",
                "Adzuna",
                0,
                "2026-01-01",
                1
            ))

            cursor.execute("""
                INSERT INTO jobs
                (
                    title, company, location, url, score,
                    date_found, source, applied, last_seen, active
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                "Old Reed Job",
                "Company B",
                "Liverpool",
                "https://example.com/reed-old",
                10,
                "2026-01-01",
                "Reed",
                0,
                "2026-01-01",
                1
            ))

            connection.commit()
            connection.close()

            mark_stale_jobs_inactive(
                days_old=14,
                database_name=database_path,
                source="Adzuna"
            )

            connection = sqlite3.connect(database_path)
            cursor = connection.cursor()

            cursor.execute("""
                SELECT active
                FROM jobs
                WHERE source = 'Adzuna'
            """)
            adzuna_active = cursor.fetchone()[0]

            cursor.execute("""
                SELECT active
                FROM jobs
                WHERE source = 'Reed'
            """)
            reed_active = cursor.fetchone()[0]

            connection.close()

            self.assertEqual(adzuna_active, 0)
            self.assertEqual(reed_active, 1)






if __name__ == "__main__":
    unittest.main()