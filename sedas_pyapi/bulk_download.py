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

import logging
import os
import queue
import threading
import time
from getpass import getpass
import json

from sedas_pyapi.sedas_api import SeDASAPI

_logger = logging.getLogger("bulk_downloader")


class SeDASBulkDownload:

    def __init__(self, sedas_client: SeDASAPI, download_prefix: str, parallel=2, done_queue: queue.Queue = None):
        """
        create a new SeDASBulkDownloader
        :param sedas_client: the client to use for downloading
        :param download_prefix: where to download the files to.
        :param parallel: the number of download threads to use. There will always be one request thread.
        :param done_queue: a queue which completed downloads will be added to. Allows other parts of the program to be
                           notified when a download completes.
        """
        self._client = sedas_client
        self._prefix = download_prefix
        self._done_queue = done_queue
        self._pending_download = queue.Queue()  # products ready to download.
        self._pending_request_ids = []  # list of request ids that are currently pending
        self._pending_products = {}  # maps request id to product object
        self._shut_down = False  # should this downloader shutdown at the next safe point.
        self._requested_thread = None
        self._download_threads = []
        self._monitor_thread = None
        self._parallel = parallel
        self._current_downloads = 0  # Number of currently in progress downloads.

        self.start()

    def start(self) -> None:
        """
        Start all the required background threads for this Bulk Download operation.

        Note: you shouldn't normally need to call this. It is called by constructing a SeDASBulkDownload class.
        :return: None
        """
        if self._requested_thread:
            raise ChildProcessError("already started the downloader")
        self._requested_thread = threading.Thread(target=self._requests, args=())
        self._requested_thread.daemon = True
        self._requested_thread.start()

        for i in range(self._parallel):
            self._download_threads.append(threading.Thread(target=self._downloads, args=()))
            self._download_threads[i].daemon = True
            self._download_threads[i].start()

        self._monitor_thread = threading.Thread(target=self._monitor, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def shutdown(self) -> None:
        """
        Flag that this download operation should stop at the next safe point.

        This will not stop the background threads. When they have finished what they are doing they will shut down
        :return: None
        """
        self._shut_down = True

    def is_done(self) -> bool:
        """
        Has all the work for this Bulk Download operation been completed.
        :return: true if all the requested work is done.
        """
        return self._pending_download.empty() and len(self._pending_request_ids) == 0 and self._current_downloads == 0

    def add(self, search_results: []) -> None:
        """
        Add a list of products to be downloaded
        :param search_results: list of products from a search
        :return: None
        """
        for product in search_results:

            if 'downloadUrl' in product:
                self._pending_download.put(product)
            else:
                # if we haven't submitted a request for this one already...
                if product not in self._pending_products.items():
                    request_id = self._client.request(product)
                    self._pending_request_ids.append(request_id)
                    self._pending_products[request_id] = product

    def _monitor(self) -> None:
        """
        A monitor thread to log download and request progress.
        :return:
        """
        while not self._shut_down:
            _logger.info(f"{self._pending_download.qsize()} downloads pending, "
                         f"{self._current_downloads} downloads in progress, "
                         f"{len(self._pending_products)} requests pending")

            time.sleep(5)
        _logger.debug("monitor thread stopping")

    def _requests(self) -> None:
        """
        Thread function to keep an eye on the pending requests and move them to the download queue when they are ready
        :return: None
        """
        while not self._shut_down:
            time.sleep(5)  # wait a little bit so requests have a chance to complete and we don't hammer SeDAS
            # Now check on the state of our pending requests
            for request_id in self._pending_request_ids:
                product = self._pending_products[request_id]
                _logger.debug(f"checking state of request {request_id} for {product['supplierId']}")
                download_url = self._client.is_request_ready(request_id)
                if download_url:
                    _logger.info(f"Request {request_id} COMPLETE for {product['supplierId']}")
                    product['downloadUrl'] = download_url
                    self._pending_download.put(product)
                    del self._pending_products[request_id]
                    self._pending_request_ids.remove(request_id)
        _logger.debug("requests thread stopping")

    def _downloads(self) -> None:
        """
        Thread function to download the files. Several of these will likely be running.
        :return: None
        """
        while not self._shut_down:
            time.sleep(1)
            _logger.debug(f"{self._pending_download.qsize()} downloads pending")
            try:
                pending = self._pending_download.get()
                self._current_downloads = self._current_downloads + 1
                name = os.path.join(self._prefix, pending['supplierId'] + '.zip')
                _logger.info(f"downloading {pending['supplierId']} to {name}")
                self._client.download(pending, name)
                self._current_downloads = self._current_downloads - 1
                if self._done_queue:
                    self._done_queue.put({'search': pending, 'path': name})
            except queue.Empty:
                time.sleep(1)
        _logger.debug("download thread stopping")


if __name__ == '__main__':
    """
    The following is an example of searching and then downloading a selection of images over an aoi.
    
    It will print out the search result objects as it goes.
    Logging is set to debug so it will be very chatty, but this gives a better idea around what is going on.
    """
    wkt = "POLYGON ((-1.3295 51.5881," \
          "-1.3013 51.5872," \
          "-1.3020 51.5621," \
          "-1.3300 51.5622," \
          "-1.3295 51.5881))"
    startDate = "2019-04-30T00:00:00Z"
    endDate = "2019-05-12T23:59:59Z"

    output_path = "/tmp/"

    _username = input("Please enter your username:")
    __password = getpass("Please enter your password:")

    # Note the SeDASBulkDownload is very chatty at debug. But if you need to know what is going on enable logging.
    logging.basicConfig(level=logging.DEBUG)
    _logger.setLevel(logging.DEBUG)

    sedas = SeDASAPI(_username, __password)

    print("search by aoi and sensor type...")
    result = sedas.search_sar(wkt, startDate, endDate, sarProductType="SLC")
    print(json.dumps(result, sort_keys=True, indent=4, separators=(',', ': ')))

    print("single product query...")
    singleProduct = sedas.search_product("S1B_IW_GRDH_1SDV_20190528T105030_20190528T105055_016443_01EF3E_5E4F")
    print(json.dumps(singleProduct, sort_keys=True, indent=4, separators=(',', ': ')))

    print("Downloading results of aoi search...")

    done_queue = queue.Queue()

    downloader = SeDASBulkDownload(sedas, output_path, parallel=3, done_queue=done_queue)
    downloader.add(result['products'])
    while not downloader.is_done():
        try:
            completed = done_queue.get()
            print(completed)
        except queue.Empty:
            time.sleep(5)
    downloader.shutdown()
    print("Download complete!")
