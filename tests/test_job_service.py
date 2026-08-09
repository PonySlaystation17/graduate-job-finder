import unittest
from unittest.mock import patch

from job_service import (
    get_rejection_reasons,
    create_job_key,
    process_jobs
)

class TestJobService(unittest.TestCase):

    def test_good_graduate_software_job_is_accepted(self):
        job = {
            "title": "Graduate Software Engineer",
            "description": "Python developer role",
            "location": "Liverpool",
            "salary_min": 32000
        }

        reasons = get_rejection_reasons(job)

        self.assertEqual(reasons, [])

    def test_senior_experience_requirement_is_rejected(self):
        job = {
            "title": "Graduate Software Engineer",
            "description": "Python role requiring 5+ years experience",
            "location": "Liverpool",
            "salary_min": 35000
        }

        reasons = get_rejection_reasons(job)

        self.assertIn("Experience level too high", reasons)

    def test_low_known_salary_is_rejected(self):
        job = {
            "title": "Junior Software Developer",
            "description": "Java developer role",
            "location": "Manchester",
            "salary_min": 25000
        }

        reasons = get_rejection_reasons(job)

        self.assertIn("Salary below minimum", reasons)

    def test_missing_salary_is_not_rejected(self):
        job = {
            "title": "Junior Software Developer",
            "description": "Java developer role",
            "location": "Manchester",
            "salary_min": 0
        }

        reasons = get_rejection_reasons(job)

        self.assertNotIn("Salary below minimum", reasons)

    def test_create_job_key_normalises_job_details(self):
        job = {
            "title": "  Graduate Software Engineer ",
            "company": "Example LTD ",
            "location": " Liverpool "
        }

        key = create_job_key(job)

        self.assertEqual(
            key,
            (
                "graduate software engineer",
                "example ltd",
                "liverpool"
            )
        )

    @patch("job_service.save_job_to_db")
    def test_process_jobs_separates_matches_and_rejections(self, mock_save):
        jobs = [
            {
                "source": "Test",
                "title": "Graduate Software Engineer",
                "company": "Good Company",
                "location": "Liverpool",
                "description": "Python developer role",
                "url": "https://example.com/good",
                "salary_min": 32000,
                "salary_max": 35000
            },
            {
                "source": "Test",
                "title": "Senior Sales Manager",
                "company": "Wrong Company",
                "location": "Liverpool",
                "description": "Sales management role",
                "url": "https://example.com/bad",
                "salary_min": 50000,
                "salary_max": 60000
            }
        ]

        matched_jobs, rejected_jobs = process_jobs(jobs)

        self.assertEqual(len(matched_jobs), 1)
        self.assertEqual(len(rejected_jobs), 1)

        self.assertEqual(
            matched_jobs[0]["title"],
            "Graduate Software Engineer"
        )

        self.assertEqual(
            rejected_jobs[0]["title"],
            "Senior Sales Manager"
        )

        mock_save.assert_called_once()

    @patch("job_service.save_job_to_db")
    @patch("builtins.print")
    def test_process_jobs_reports_only_new_matches(self, mock_print, mock_save):
        mock_save.side_effect = [True, False]

        jobs = [
            {
                "source": "Test",
                "title": "Graduate Software Engineer",
                "company": "Company A",
                "location": "Liverpool",
                "description": "Python developer role",
                "url": "https://example.com/1",
                "salary_min": 32000,
                "salary_max": 35000
            },
            {
                "source": "Test",
                "title": "Junior Java Developer",
                "company": "Company B",
                "location": "London",
                "description": "Java software developer role",
                "url": "https://example.com/2",
                "salary_min": 33000,
                "salary_max": 36000
            }
        ]

        process_jobs(jobs)

        mock_print.assert_called_with(
    "----- New matches found: 1 -----"
)




if __name__ == "__main__":
    unittest.main()