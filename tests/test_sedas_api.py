"""
Copyright 2019 Satellite Applications Catapult

   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at

       http://www.apache.org/licenses/LICENSE-2.0

   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""

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

    def test_blank_username(self):
        self.assertRaises(
            ValueError,
            SeDASAPI,
            "",
            "is not a real password"
        )

    def test_blank_password(self):
        self.assertRaises(
            ValueError,
            SeDASAPI,
            "is not a real username",
            ""
        )
