import os
import queue
import threading
import time


class SeDASBulkDownload:

    def __init__(self, sedas_client, download_prefix, parallel=2, verbose=False):
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
        self._shut_down = False # should this downloader shutdown at the next safe point.
        self._requested_thread = None
        self._download_threads = []
        self._parallel = parallel
        self._current_downloads = 0  # Number of currently in progress downloads.

        # TODO: find what the best logger to use is based on what tools that the science team uses.
        self._verbose = verbose

        self.start()

    def start(self):
        if self._requested_thread:
            raise ChildProcessError("already started the downloader")
        self._requested_thread = threading.Thread(target=self.requests, args=())
        self._requested_thread.daemon = True
        self._requested_thread.start()

        for i in range(self._parallel):
            t = threading.Thread(target=self.downloads, args=())
            t.daemon = True
            t.start()
            self._download_threads.append(t)

    def shutdown(self):
        self._shut_down = True

    def is_done(self):
        return self._pending_download.empty() and len(self._pending_request_ids) == 0 and self._current_downloads == 0

    def add(self, search_results):
        for product in search_results:

            if 'downloadUrl' in product:
                self._pending_download.put(product)
            else:
                # if we haven't submitted a request for this one already...
                if product not in self._pending_products.items():
                    request_id = self._client.request(product)
                    self._pending_request_ids.append(request_id)
                    self._pending_products[request_id] = product

    def requests(self):
        while not self._shut_down:
            time.sleep(5)  # wait a little bit so requests have a chance to complete and we don't hammer SeDAS
            # Now check on the state of our pending requests
            for request_id in self._pending_request_ids:
                product = self._pending_products[request_id]
                if self._verbose:
                    print(f"checking state of request {request_id} for {product['supplierId']}")
                download_url = self._client.is_request_ready(request_id)
                if download_url:
                    if self._verbose:
                        print(f"request {request_id} COMPLETE for {product['supplierId']}")
                    product['downloadUrl'] = download_url
                    self._pending_download.put(product)
                    del self._pending_products[request_id]
                    self._pending_request_ids.remove(request_id)

    def downloads(self):
        while not self._shut_down:
            if self._verbose:
                print(f"{self._pending_download.qsize()} downloads pending")
            try:
                pending = self._pending_download.get()
                self._current_downloads = self._current_downloads + 1
                name = os.path.join(self._prefix, pending['supplierId'] + '.zip')
                if self._verbose:
                    print(f"downloading {pending['supplierId']} to {name}")
                self._client.download(pending, name)
                self._current_downloads = self._current_downloads - 1
            except queue.Empty:
                time.sleep(1)
