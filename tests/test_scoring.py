import unittest

from scoring import score_job


class TestScoreJob(unittest.TestCase):

    def test_scores_graduate_java_role(self):
        result = score_job(
            "graduate java software engineer",
            "python backend",
            "london",
            35000
        )

        expected = (
            22,
            ["SE-title", "java-title", "python", "backend"]
        )

        self.assertEqual(result, expected)

    def test_penalises_unsuitable_sales_role(self):
        result = score_job(
            "junior sales consultant",
            "",
            "london",
            0
        )

        expected = (-10, [])

        self.assertEqual(result, expected)

if __name__ == "__main__":
    unittest.main()