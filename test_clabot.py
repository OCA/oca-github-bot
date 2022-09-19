import json
import unittest

import clabot


class ClabotTest(unittest.TestCase):
    def setUp(self):
        self.commits1 = json.load(open("test_data/commits_1.json"))
        self.commits2 = json.load(open("test_data/commits_2.json"))

    def test_get_authors_1(self):
        login, no_login = set(), set()
        for commit in self.commits1:
            u_login, u_no_login = clabot.get_commit_author(commit)
            login |= u_login
            no_login |= u_no_login
        expected_login = {
            "oca-transbot",
            "sergio-teruel",
            "oca-travis",
            "OCA-git-bot",
            "hegenator",
        }
        self.assertEqual(login, expected_login)
        self.assertEqual(no_login, set())

    def test_get_authors_2(self):
        login, no_login = set(), set()
        for commit in self.commits2:
            u_login, u_no_login = clabot.get_commit_author(commit)
            login |= u_login
            no_login |= u_no_login
        expected_login = {
            "oscarolar",
            "lreficent",
            "acysos",
            "mreficent",
            "sbidoul",
            "gurneyalex",
            "bistaray",
            "hbrunn",
            "paulius-sladkevicius",
            "oca-transbot",
            "yvaucher",
            "oca-travis",
            "raycarnes",
            "pedrobaeza",
        }
        self.assertEqual(login, expected_login)
        self.assertEqual(
            no_login, {("Daniels Andersons", "daniels.andersons@avoin.systems")}
        )


if __name__ == "__main__":
    unittest.main()
