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
    sensor_url = f"{base_url}sensors"
    headers = {"Content-Type": "application/json", "Authorization": None}

    _token = None
    _token_time = None

    def __init__(self, username: str, password: str) -> None:
        self._username = username
        self.__password = password
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
            wkt: str,
            start_date: str,
            end_date: str,
            sensor: str = 'All',
            retry: bool = True,
            satellite_name: str = "",
            source_group: str = "",
            **filters
    ) -> dict:
        """
        Search the SeDAS system for products with the given parameters.

        For valid _filters parameters see https://geobrowser.satapps.org/docs/json_ProductFilters.html

        :param wkt: wkt formatted aoi
        :param start_date: start date of search in ISO8601 format
        :param end_date: end date of search in ISO8601 format
        :param sensor: the type of data to search for.  Accepts All, SAR or Optical.  Defaults to All
        :param retry: should the request be retried if it fails.
        :param satellite_name: name of the satellite to search
        :param source_group: name of the source group to search
        :param filters: filter search on
        :return: list of search results
        """
        self.login()

        query = {
            'sensorFilters': {"type": sensor},
            'filters': filters,
            'aoiWKT': wkt,
            'start': start_date,
            'stop': end_date
        }
        if satellite_name:
            query['satelliteName'] = satellite_name

        if source_group:
            query['sourceGroup'] = source_group

        req = Request(self.search_url, json.dumps(query).encode(), headers=self.headers)
        try:
            resp = urlopen(req)
            return json.load(resp)
        except HTTPError as e:
            if self._error_handling(e) and retry:
                return self.search(
                    wkt,
                    start_date,
                    end_date,
                    sensor,
                    retry=False,
                    satellite_name=satellite_name,
                    **filters
                )

    def search_sar(
            self,
            wkt: str,
            start_date: str,
            end_date: str,
            satellite_name: str = "",
            source_group: str = "",
            **filters
    ) -> dict:
        """
        Search the SeDAS system for SAR products only with the given parameters

        For valid _filters parameters see https://geobrowser.satapps.org/docs/json_ProductFilters.html

        :param wkt: wkt formatted aoi
        :param start_date: start date of search in ISO8601 format
        :param end_date: end date of search in ISO8601 format
        :param satellite_name: name of the satellite to search
        :param source_group: name of the source group to search
        :param filters: filter search on
        :return: list of search results
        """
        return self.search(
            wkt,
            start_date,
            end_date,
            'SAR',
            satellite_name=satellite_name,
            source_group=source_group,
            **filters
        )

    def search_optical(
            self,
            wkt: str,
            start_date: str,
            end_date: str,
            satellite_name: str = "",
            source_group: str = "",
            **filters
    ) -> dict:
        """
        Search the SeDAS system for Optical products only with the given parameters

        For valid _filters parameters see https://geobrowser.satapps.org/docs/json_ProductFilters.html

        :param wkt: wkt formatted aoi
        :param start_date: start date of search in ISO8601 format
        :param end_date: end date of search in ISO8601 format
        :param satellite_name: name of the satellite to search
        :param source_group: name of the source group to search
        :param filters: filter search on
        :return: list of search results
        """
        return self.search(
            wkt,
            start_date,
            end_date,
            'Optical',
            satellite_name=satellite_name,
            source_group=source_group,
            **filters
        )

    def search_product(self, product_id: str, retry: bool = True) -> dict:
        """
        Search for information about a known product id.
        :param product_id: product id to look for
        :param retry: Should the request be retried on error.
        :return: search result dictionary
        """
        self.login()
        url = f"{self.search_url}/products?ids={product_id}"
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req) as resp:
                return json.load(resp)
        except HTTPError as e:
            if self._error_handling(e) and retry:
                return self.search_product(product_id, retry=False)

    def list_sensor_groups(self, retry: bool = True) -> dict:
        """
        Search for information about available source groups.
        :param retry: Should the request be retried on error.
        :return: search result dictionary
        """
        self.login()
        url = f"{self.sensor_url}/sourceGroups"
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req) as resp:
                return json.load(resp)
        except HTTPError as e:
            if self._error_handling(e) and retry:
                return self.list_sensor_groups(retry=False)

    def list_satellites(self, retry: bool = True) -> dict:
        """
        Search for information about available satellites.
        :param retry: Should the request be retried on error.
        :return: search result dictionary
        """
        self.login()
        url = f"{self.sensor_url}/satellites"
        req = Request(url, headers=self.headers)
        try:
            with urlopen(req) as resp:
                return json.load(resp)
        except HTTPError as e:
            if self._error_handling(e) and retry:
                return self.list_satellites(retry=False)

    def download(self, product, output_path: str, retry: bool = True) -> None:
        """
        Download a product from sedas
        :param product: product dictionary from a search
        :param output_path: where to put the output file
        :param retry: Should the request be retried on error.
        :return: None
        """
        with self.download_request(product, retry) as resp:
            with open(output_path, "+wb") as f:
                shutil.copyfileobj(resp, f)

    def download_request(self, product: dict, retry: bool = True):
        """
        Download a product from sedas, returning the request object.
        Use this over the download function when you don't want the data to touch disk before you do something with it.
        :param product: product dictionary from a search
        :param retry: Should the request be retried on error.
        :return: response object that can be read to download the file.
        """
        self.login()
        url = product['downloadUrl']
        if not url:
            raise AttributeError("no download url defined for product")
        req = Request(url, headers=self.headers)
        try:
            return urlopen(req)
        except HTTPError as e:
            if self._error_handling(e) and retry:
                return self.download_request(product, retry=False)

    def request(self, product, retry: bool = True) -> str:
        """
        Request a file from the SeDAS long term archive
        :param product: product to request from the search
        :param retry: Should the request be retried on error.
        :return: Request ID
        """
        self.login()
        url = f"{self.base_url}/request/{product['supplierId']}"
        req = Request(url, headers=self.headers, method="POST")
        try:
            resp = urlopen(req)
            return json.load(resp)['requestId']
        except HTTPError as e:
            if self._error_handling(e) and retry:
                return self.request(product, retry=False)

    def is_request_ready(self, request_id: str, retry: bool = True):
        """
        checks on the status of a request. If it is complete it will return the download url
        :param request_id: request id to check on.
        :param retry: Should the request be retried on error.
        :return: download url if the request is complete, None otherwise
        """
        self.login()
        url = f"{self.base_url}/request?ids={request_id}"
        req = Request(url, headers=self.headers)
        try:
            decoded = json.load(urlopen(req))
            if len(decoded) >= 1 and 'downloadUrl' in decoded[0]:
                return decoded[0]['downloadUrl']
            return None
        except HTTPError as e:
            if self._error_handling(e) and retry:
                return self.is_request_ready(request_id, retry=False)

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
