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
            21,
            ["SE-title", "java-title", "python", "backend"]
        )

        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()