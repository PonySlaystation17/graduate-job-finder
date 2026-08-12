import requests
import unittest
from unittest.mock import patch, Mock

from importers.adzuna import fetch_jobs_adzuna


class TestAdzunaImporter(unittest.TestCase):

    @patch("importers.adzuna.requests.get")
    def test_fetch_jobs_adzuna_converts_job_to_standard_format(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "title": "Graduate Software Engineer",
                    "company": {
                        "display_name": "Example Ltd"
                    },
                    "location": {
                        "display_name": "Liverpool"
                    },
                    "description": "Graduate Python developer role",
                    "redirect_url": "https://example.com/job/1"
                }
            ]
        }

        mock_get.return_value = mock_response

        jobs, success = fetch_jobs_adzuna()

        self.assertTrue(success)
        self.assertGreater(len(jobs), 0)

        job = jobs[0]

        self.assertEqual(job["source"], "Adzuna")
        self.assertEqual(job["title"], "Graduate Software Engineer")
        self.assertEqual(job["company"], "Example Ltd")
        self.assertEqual(job["location"], "Liverpool")
        self.assertEqual(job["description"], "Graduate Python developer role")
        self.assertEqual(job["url"], "https://example.com/job/1")

    @patch("importers.adzuna.requests.get")
    def test_fetch_jobs_adzuna_handles_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout

        jobs, success = fetch_jobs_adzuna()

        self.assertEqual(jobs, [])
        self.assertFalse(success)

    @patch("importers.adzuna.requests.get")
    def test_fetch_jobs_adzuna_handles_invalid_json(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.side_effect = requests.exceptions.JSONDecodeError(
            "Invalid JSON",
            "",
            0
        )

        mock_get.return_value = mock_response

        jobs, success = fetch_jobs_adzuna()

        self.assertEqual(jobs, [])
        self.assertFalse(success)



if __name__ == "__main__":
    unittest.main()