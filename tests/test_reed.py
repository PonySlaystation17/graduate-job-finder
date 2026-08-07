import unittest
from unittest.mock import patch, Mock
import requests
from importers.reed import fetch_jobs_reed


class TestReedImporter(unittest.TestCase):

    @patch("importers.reed.requests.get")
    def test_fetch_jobs_reed_converts_job_to_standard_format(self, mock_get):
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "results": [
                {
                    "jobTitle": "Graduate Software Engineer",
                    "employerName": "Example Ltd",
                    "locationName": "Liverpool",
                    "jobDescription": "Graduate Python developer role",
                    "jobUrl": "https://example.com/job/1",
                    "minimumSalary": 30000,
                    "maximumSalary": 35000
                }
            ]
        }

        mock_get.return_value = mock_response

        jobs, success = fetch_jobs_reed()

        self.assertTrue(success)
        self.assertGreater(len(jobs), 0)

        job = jobs[0]

        self.assertEqual(job["source"], "Reed")
        self.assertEqual(job["title"], "Graduate Software Engineer")
        self.assertEqual(job["company"], "Example Ltd")
        self.assertEqual(job["location"], "Liverpool")
        self.assertEqual(job["description"], "Graduate Python developer role")
        self.assertEqual(job["url"], "https://example.com/job/1")
        self.assertEqual(job["salary_min"], 30000)
        self.assertEqual(job["salary_max"], 35000)

    @patch("importers.reed.requests.get")
    def test_fetch_jobs_reed_handles_timeout(self, mock_get):
        mock_get.side_effect = requests.exceptions.Timeout

        jobs, success = fetch_jobs_reed()

        self.assertEqual(jobs, [])
        self.assertFalse(success)






if __name__ == "__main__":
    unittest.main()