import json
import shutil
import time
from getpass import getpass
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from getthestuff.bulk_download import SeDASBulkDownload

class SeDASAPI:
    """
    SeDASAPI provides easy access to the SeDAS API.

    Create an instance of this object providing your username and password.
    Then use this class to search for data or download data.

    See the main at the end of this file for examples of how to use this.
    """
    base_url = "https://geobrowser.satapps.org/api/"
    authentication_url = f"{base_url}authentication"
    search_url = f"{base_url}search"
    headers = {"Content-Type": "application/json", "Authorization": None}

    _token = None

    def __init__(self, _username, __password):
        self._username = _username
        self.__password = __password
        self.login()

    def login(self):
        """
        Log into the sedas platform.

        :return: access token if login was successful.
        """
        data = {'username': self._username, 'password': self.__password}

        req = Request(
            self.authentication_url,
            json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        try:
            self._token = json.load(urlopen(req))['token']
            self.headers['Authorization'] = f"Token {self._token}"
        except HTTPError as e:
            print(e)
            print(e.read().decode())
            raise e

    def search(self, _wkt, _start_date, _end_date, _sensor='All', **_filters):
        """
        Search the SeDAS system for products with the given parameters.
        :param _wkt: wkt formatted aoi
        :param _start_date: start date of search in ISO8601 format
        :param _end_date: end date of search in ISO8601 format
        :param _sensor: the type of data to search for.  Accepts All, SAR or Optical.  Defaults to All
        :param _filters: filter search on
        :return: list of search results
        """
        query = {
            'sensorFilters': {"type": _sensor},
            'filters': _filters,
            'aoiWKT': _wkt,
            'start': _start_date,
            'stop': _end_date
        }
    
        req = Request(self.search_url, json.dumps(query).encode(), headers=self.headers)
        try:
            resp = urlopen(req)
            return json.load(resp)
        except HTTPError as e:
            print(e)
            print(e.read().decode())
            raise e

    def search_sar(self, _wkt, _start_date, _end_date, **_filters):
        """
        Search the SeDAS system for SAR products only with the given parameters
        :param _wkt: wkt formatted aoi
        :param _start_date: start date of search in ISO8601 format
        :param _end_date: end date of search in ISO8601 format
        :param _filters: filter search on
        :return: list of search results
        """
        return self.search(_wkt, _start_date, _end_date, 'SAR', **_filters)

    def search_optical(self, _wkt, _start_date, _end_date, **_filters):
        """
        Search the SeDAS system for Optical products only with the given parameters
        :param _wkt: wkt formatted aoi
        :param _start_date: start date of search in ISO8601 format
        :param _end_date: end date of search in ISO8601 format
        :param _filters: filter search on
        :return: list of search results
        """
        return self.search(_wkt, _start_date, _end_date, 'Optical', **_filters)

    def search_product(self, _product_id):
        """
        Search for information about a known product id.
        :param _product_id: product id to look for
        :return: search result dictionary
        """
        url = f"{self.search_url}/products?ids={_product_id}"
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req) as resp:
                return json.load(resp)
        except HTTPError as e:
            print(e)
            print(e.read().decode())
            raise e

    def download(self, _product, _output_path):
        """
        download a product from sedas
        :param _product: product dictionary from a search
        :param _output_path: where to put the output file
        :return: None
        """
    
        url = _product['downloadUrl']
        if not url:
            raise AttributeError("no download url defined for product")
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req) as resp:
                # TODO: consider a version of this function that returns the resp object so it doesn't have to touch the
                #  disk in cases where that is better
                with open(_output_path, "+wb") as f:
                    shutil.copyfileobj(resp, f)
        except HTTPError as e:
            print(e)
            print(e.read().decode())
            raise e

    def request(self, _product):
        """
        Request a file from the SeDAS long term archive
        :param _product: product to request from the search
        :return: Request ID
        """
        url = f"{self.base_url}/request/{_product['supplierId']}"
        req = Request(url, headers=self.headers, method="POST")
        try:
            resp = urlopen(req)
            return json.load(resp)['requestId']
        except HTTPError as e:
            print(e)
            print(e.read().decode())
            raise e

    def is_request_ready(self, _request_id):
        """
        checks on the status of a request. If it is complete it will return the download url
        :param _request_id: request id to check on.
        :return: download url if the request is complete, None otherwise
        """
        url = f"{self.base_url}/request?ids={_request_id}"
        req = Request(url, headers=self.headers)
        try:
            decoded = json.load(urlopen(req))
            if len(decoded) > 1 and 'downloadUrl' in decoded[0]:
                return decoded[0]['downloadUrl']
            return None
        except HTTPError as e:
            print(e)
            print(e.read().decode())
            raise e


if __name__ == '__main__':
    wkt = "POLYGON ((-78.0294047453918 7.54828534191209," \
          "-75.5410318208992 4.9335544228762," \
          "-73.5283895711597 6.84893487157956," \
          "-76.0167624956523 9.46366579061545," \
          "-78.0294047453918 7.54828534191209))"
    startDate = "2017-04-30T00:00:00Z"
    endDate = "2017-05-12T23:59:59Z"

    output_path = "/tmp/"

    _username = input("Please enter your username:")
    __password = getpass("Please enter your password:")

    sedas = SeDASAPI(_username, __password)

    print("search by aoi and sensor type...")
    result = sedas.search(wkt, startDate, endDate, "SAR")
    print(json.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))

    print("single product query...")
    singleProduct = sedas.search_product("S1B_IW_GRDH_1SDV_20190528T105030_20190528T105055_016443_01EF3E_5E4F")
    print(json.dumps(singleProduct, sort_keys=True, indent=4, separators=(',', ': ')))

    print("Downloading results of aoi search...")

    downloader = SeDASBulkDownload(sedas, output_path, parallel=3, verbose=True)
    downloader.add(result['products'])
    while not downloader.is_done():
        time.sleep(5)
    downloader.shutdown()
    print("Download complete!")
