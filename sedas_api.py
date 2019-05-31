import os
import shutil
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from getpass import getpass
import json


class SeDASAPI:
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
        self._token = json.load(urlopen(req))['token']
        self.headers['Authorization'] = f"Token {self._token}"

    def search(self, _wkt, _start_date, _end_date, _sensor='All', **_filters):
        """
        Search the SeDAS system for products with the given parameters
        :param _wkt: wkt formatted aoi
        :param _start_date: start date of search in ISO8601 format
        :param _end_date: end date of search in ISO8601 format
        :parma _sensor: the type of data to search for.  Accepts All, SAR or Optical.  Defaults to All
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
        with urlopen(req) as resp:
            with open(_output_path, "+wb") as f:
                shutil.copyfileobj(resp, f)

    def request(self, _product):
        """
        Request a file from the SeDAS long term archive
        :param _product: product to request from the search
        :return: Request ID
        """
        url = f"{self.base_url}/request/{_product['supplierId']}"
        req = Request(url, headers=self.headers, method="POST")
        resp = urlopen(req)
        return json.load(resp)['requestId']

    def is_request_ready(self, _request_id):
        """
        checks on the status of a request. If it is complete it will return the download url
        :param _request_id: request id to check on.
        :return: download url if the request is complete, None otherwise
        """
        url = f"{self.base_url}/request?ids={_request_id}"
        req = Request(url, headers=self.headers)
        decoded = json.load(urlopen(req))
        if len(decoded) > 1 and 'downloadUrl' in decoded[0]:
            return decoded[0]['downloadUrl']
        return None


if __name__ == '__main__':
    wkt = "POLYGON ((-78.0294047453918 7.54828534191209,-75.5410318208992 4.9335544228762,-73.5283895711597 6.84893487157956,-76.0167624956523 9.46366579061545,-78.0294047453918 7.54828534191209))"
    startDate = "2019-04-30T00:00:00Z"
    endDate = "2019-05-30T23:59:59Z"

    output_path = "/tmp/"

    _username = input("Please enter your username:")
    __password = getpass("Please enter your password:")
    sedas = SeDASAPI(_username, __password)
    result = sedas.search("SAR", wkt, startDate, endDate)
    print(json.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))

    for product in result['products']:
        o = os.path.join(output_path, product['supplierId'] + ".zip")
        if 'downloadURL' in product:
            print(f"downloading {product['supplierId']} to {o}")
            sedas.download(product, o)
        else:
            print(f"no download url for {product['supplierId']} submitting lta request")
            request_id = sedas.request(product)
            dl = sedas.is_request_ready(request_id)
            while not dl:
                time.sleep(5)
                print(f"checking on {request_id} for {product['supplierId']} again...")
                dl = sedas.is_request_ready(request_id)
            print("downloading {product['supplierId']} to {o}")
            product["downloadUrl"] = dl
            sedas.download(product, o)
