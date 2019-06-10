import logging
import os
import queue
import threading
import time
from getpass import getpass
import json

from getthestuff.sedas_api import SeDASAPI

_logger = logging.getLogger("bulk_downloader")


class SeDASBulkDownload:

    def __init__(self, sedas_client: SeDASAPI, download_prefix: str, parallel=2):
        """
        create a new SeDASBulkDownloader
        :param sedas_client: the client to use for downloading
        :param download_prefix: where to download the files to.
        :param parallel: the number of download threads to use. There will always be one request thread.
        :param verbose: enable printing of current working state to stdout.
        """
        self._client = sedas_client
        self._prefix = download_prefix
        self._pending_download = queue.Queue()  # products ready to download.
        self._pending_request_ids = []  # list of request ids that are currently pending
        self._pending_products = {}  # maps request id to product object
        self._shut_down = False  # should this downloader shutdown at the next safe point.
        self._requested_thread = None
        self._download_threads = []
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
            t = threading.Thread(target=self._downloads, args=())
            t.daemon = True
            t.start()
            self._download_threads.append(t)

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
                    _logger.debug(f"request {request_id} COMPLETE for {product['supplierId']}")
                    _logger.debug(f"Adding {product['supplierId']} to download queue")
                    product['downloadUrl'] = download_url
                    self._pending_download.put(product)
                    del self._pending_products[request_id]
                    self._pending_request_ids.remove(request_id)

    def _downloads(self) -> None:
        """
        Thread function to download the files. Several of these will likely be running.
        :return: None
        """
        while not self._shut_down:
            _logger.debug(f"{self._pending_download.qsize()} downloads pending")
            try:
                pending = self._pending_download.get()
                self._current_downloads = self._current_downloads + 1
                name = os.path.join(self._prefix, pending['supplierId'] + '.zip')
                _logger.debug(f"downloading {pending['supplierId']} to {name}")
                self._client.download(pending, name)
                self._current_downloads = self._current_downloads - 1
            except queue.Empty:
                time.sleep(1)


if __name__ == '__main__':
    """
    The following is an example of 
    """
    wkt = "POLYGON ((-1.32956397342894 51.5881719478951," \
          "-1.30138872523889 51.5872200814022," \
          "-1.30208676066703 51.5621542637557," \
          "-1.33007163555849 51.5622177215219," \
          "-1.32956397342894 51.5881719478951))"
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

    downloader = SeDASBulkDownload(sedas, output_path, parallel=3)
    downloader.add(result['products'])
    while not downloader.is_done():
        time.sleep(5)
    downloader.shutdown()
    print("Download complete!")
