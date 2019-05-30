import os
import shutil
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from getpass import getpass
import json


class SeDASAPI:
    authentication_url = "https://geobrowser.satapps.org/api/authentication"
    search_url = "https://geobrowser.satapps.org/api/search"
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

    def search(self, _sensor, _wkt, _start_date, _end_date, **_filters):
        """
        search the sedas system for the given parameters
        :param _sensor: the type of sensor to query one of 'All', 'Optical', or 'SAR'
        :param _wkt: wkt formatted aoi
        :param _start_date: start date to look for
        :param _end_date: end date to look for
        :param _filters: other parameters
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
        print(f"downloading {product['supplierId']} to {o}")
        sedas.download(product, o)
