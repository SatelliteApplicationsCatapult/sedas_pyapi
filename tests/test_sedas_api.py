import unittest
from urllib.error import HTTPError

from getthestuff.sedas_api import SeDASAPI


class TestSeDASAPI(unittest.TestCase):
    def test_login_bad_creds(self):
        self.assertRaises(
            HTTPError,
            SeDASAPI,
            "bogus",
            "arewyt qu3herilsuhfgloiheloixyhgndikukxjfglzwothis is not a real password"
        )
