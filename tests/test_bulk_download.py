import unittest
import time

from requests import HTTPError

from sedas_pyapi.bulk_download import SeDASBulkDownload
from sedas_pyapi.sedas_api import SeDASAPI


class TestBulkDownload(unittest.TestCase):

    def test_erroredRequest(self):
        download = SeDASBulkDownload(MockSedasAPI("hello", "world"), "/tmp/")
        download.add([{"supplierId": "test"}])

        while not download.is_done():
            time.sleep(1)


# Enough of a mock SedasAPI to cover what we need.
class MockSedasAPI(SeDASAPI):
    def __init__(self, username: str, password: str) -> None:
        SeDASAPI.__init__(self, username, password)
        self._failed = False

    def login(self):
        pass

    def download(self, product, output_path: str, retry: bool = True) -> None:
        if product['downloadUrl'] == "a-mock-download-url.html" and not self._failed:
            self._failed = True
            raise HTTPError("boom")
        pass

    def request(self, product, retry: bool = True) -> str:
        return product['supplierId']

    def is_request_ready(self, request_id: str, retry: bool = True):
        return "a-mock-download-url.html"