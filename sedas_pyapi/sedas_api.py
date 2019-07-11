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

import datetime
import json
import logging
import shutil
from urllib.error import HTTPError
from urllib.request import Request, urlopen

_logger = logging.getLogger("sedas_api")


class SeDASAPI:
    """
    SeDASAPI provides easy access to the SeDAS API.

    Create an instance of this object providing your username and password.
    Then use this class to search for data or download data.
    """
    base_url = "https://geobrowser.satapps.org/api/"
    authentication_url = f"{base_url}authentication"
    search_url = f"{base_url}search"
    headers = {"Content-Type": "application/json", "Authorization": None}

    _token = None
    _token_time = None

    def __init__(self, _username: str, __password: str) -> None:
        self._username = _username
        self.__password = __password
        self.login()

    def login(self) -> None:
        """
        Log into the sedas platform.

        :return: access token if login was successful.
        """
        # if we already have a token and it is not likely to have expired yet we can skip the rest
        # of the login process
        if self._token and (self._token_time and datetime.datetime.now() > self._token_time):
            return

        # check that the username and password have been set.
        if not self._username or not self.__password:
            raise ValueError("username and password must not be blank")

        data = {'username': self._username, 'password': self.__password}

        req = Request(
            self.authentication_url,
            json.dumps(data).encode(),
            headers={"Content-Type": "application/json"}
        )
        try:
            resp = json.load(urlopen(req))
            self._token = resp['token']
            self.headers['Authorization'] = f"Token {self._token}"
            self._token_time = datetime.datetime.strptime(resp['validUntil'], "%Y-%m-%dT%H:%M:%SZ") - \
                datetime.timedelta(minutes=5)  # knock five minutes off so we log in before we need to.
            _logger.debug("successful login.")
        except HTTPError as e:
            # Note: This doesn't use the default error handling because that will try and log in again if you have
            # provided invalid login details and would get stuck in an infinite loop
            _logger.error(e)
            _logger.error(e.read().decode())
            raise e

    def search(
            self,
            _wkt: str,
            _start_date: str,
            _end_date: str,
            _sensor: str = 'All',
            _retry: bool = True,
            _satellite_name="",
            _source_group="",
            **_filters
    ) -> dict:
        """
        Search the SeDAS system for products with the given parameters.

        For valid _filters parameters see https://geobrowser.satapps.org/docs/json_ProductFilters.html

        :param _wkt: wkt formatted aoi
        :param _start_date: start date of search in ISO8601 format
        :param _end_date: end date of search in ISO8601 format
        :param _sensor: the type of data to search for.  Accepts All, SAR or Optical.  Defaults to All
        :param _retry: should the request be retried if it fails.
        :param _satellite_name: name of the satellite to search
        :param _source_group: name of the source group to search
        :param _filters: filter search on
        :return: list of search results
        """
        self.login()

        query = {
            'sensorFilters': {"type": _sensor},
            'filters': _filters,
            'aoiWKT': _wkt,
            'start': _start_date,
            'stop': _end_date
        }
        if _satellite_name:
            query['satelliteName'] = _satellite_name

        if _source_group:
            query['sourceGroup'] = _source_group

        req = Request(self.search_url, json.dumps(query).encode(), headers=self.headers)
        try:
            resp = urlopen(req)
            return json.load(resp)
        except HTTPError as e:
            if self._error_handling(e) and _retry:
                return self.search(
                    _wkt,
                    _start_date,
                    _end_date,
                    _sensor,
                    _retry=False,
                    _satellite_name=_satellite_name,
                    **_filters
                )

    def search_sar(
            self,
            _wkt: str,
            _start_date: str,
            _end_date: str,
            _satellite_name: str,
            _source_group: str,
            **_filters
    ) -> dict:
        """
        Search the SeDAS system for SAR products only with the given parameters

        For valid _filters parameters see https://geobrowser.satapps.org/docs/json_ProductFilters.html

        :param _wkt: wkt formatted aoi
        :param _start_date: start date of search in ISO8601 format
        :param _end_date: end date of search in ISO8601 format
        :param _satellite_name: name of the satellite to search
        :param _source_group: name of the source group to search
        :param _filters: filter search on
        :return: list of search results
        """
        return self.search(
            _wkt,
            _start_date,
            _end_date,
            'SAR',
            _satellite_name=_satellite_name,
            _source_group=_source_group,
            **_filters
        )

    def search_optical(
            self,
            _wkt: str,
            _start_date: str,
            _end_date: str,
            _satellite_name: str,
            _source_group: str,
            **_filters
    ) -> dict:
        """
        Search the SeDAS system for Optical products only with the given parameters

        For valid _filters parameters see https://geobrowser.satapps.org/docs/json_ProductFilters.html

        :param _wkt: wkt formatted aoi
        :param _start_date: start date of search in ISO8601 format
        :param _end_date: end date of search in ISO8601 format
        :param _satellite_name: name of the satellite to search
        :param _source_group: name of the source group to search
        :param _filters: filter search on
        :return: list of search results
        """
        return self.search(
            _wkt,
            _start_date,
            _end_date,
            'Optical',
            _satellite_name=_satellite_name,
            _source_group=_source_group,
            **_filters
        )

    def search_product(self, _product_id: str, _retry: bool = True) -> dict:
        """
        Search for information about a known product id.
        :param _product_id: product id to look for
        :param _retry: Should the request be retried on error.
        :return: search result dictionary
        """
        self.login()
        url = f"{self.search_url}/products?ids={_product_id}"
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req) as resp:
                return json.load(resp)
        except HTTPError as e:
            if self._error_handling(e) and _retry:
                return self.search_product(_product_id, _retry=False)

    def download(self, _product, _output_path: str, _retry: bool = True) -> None:
        """
        Download a product from sedas
        :param _product: product dictionary from a search
        :param _output_path: where to put the output file
        :param _retry: Should the request be retried on error.
        :return: None
        """
        with self.download_request(_product, _retry) as resp:
            with open(_output_path, "+wb") as f:
                shutil.copyfileobj(resp, f)

    def download_request(self, _product: dict, _retry: bool = True):
        """
        Download a product from sedas, returning the request object.
        Use this over the download function when you don't want the data to touch disk before you do something with it.
        :param _product: product dictionary from a search
        :param _retry: Should the request be retried on error.
        :return: response object that can be read to download the file.
        """
        self.login()
        url = _product['downloadUrl']
        if not url:
            raise AttributeError("no download url defined for product")
        req = Request(url, headers=self.headers)
        try:
            return urlopen(req)
        except HTTPError as e:
            if self._error_handling(e) and _retry:
                return self.download_request(_product, _retry=False)

    def request(self, _product, _retry: bool = True) -> str:
        """
        Request a file from the SeDAS long term archive
        :param _product: product to request from the search
        :param _retry: Should the request be retried on error.
        :return: Request ID
        """
        self.login()
        url = f"{self.base_url}/request/{_product['supplierId']}"
        req = Request(url, headers=self.headers, method="POST")
        try:
            resp = urlopen(req)
            return json.load(resp)['requestId']
        except HTTPError as e:
            if self._error_handling(e) and _retry:
                return self.request(_product, _retry=False)

    def is_request_ready(self, _request_id: str, _retry: bool = True):
        """
        checks on the status of a request. If it is complete it will return the download url
        :param _request_id: request id to check on.
        :param _retry: Should the request be retried on error.
        :return: download url if the request is complete, None otherwise
        """
        self.login()
        url = f"{self.base_url}/request?ids={_request_id}"
        req = Request(url, headers=self.headers)
        try:
            decoded = json.load(urlopen(req))
            if len(decoded) >= 1 and 'downloadUrl' in decoded[0]:
                return decoded[0]['downloadUrl']
            return None
        except HTTPError as e:
            if self._error_handling(e) and _retry:
                return self.is_request_ready(_request_id, _retry=False)

    def _error_handling(self, error: HTTPError) -> bool:
        """
        Handle errors. If this is a recoverable error by trying again this will return true.
        :param error: the HTTPError
        :return: true if this error can be recovered by logging in again.
        """
        # if we have an authentication error try and login again and then try again.
        if _is_token_error(error):
            self._token = None
            self.login()
            return True

        _logger.error(error)
        _logger.error(error.read().decode())
        raise error


def _is_token_error(error: HTTPError) -> bool:
    """
    Return true if this HTTPError is a token error.
    :param error: the error to check on
    :return: True if the error relates to a token error.
    """
    if error.code == 403 or error.code == 401:
        return True
    if error.code == 400 and hasattr(error, 'message') and error.message == "User token does not exist":
        return True
    return False
