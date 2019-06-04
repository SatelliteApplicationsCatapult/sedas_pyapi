# Get the Stuff

A small collection of useful functions to get data from SeDAS

Requires python 3+ has been tested with 3.7

## Examples

### Creating a client

```python
from getthestuff.sedas_api import SeDASAPI
from getpass import getpass

# This is a suggestion for how to get your username and password
_username = input("Please enter your username:")
__password = getpass("Please enter your password:")

sedas = SeDASAPI(_username, __password)
```

### Search for an optical AOI with cloud cover filters

```python
import json
from getthestuff.sedas_api import SeDASAPI
from getpass import getpass

wkt = "POLYGON ((-78.0294047453918 7.54828534191209," \
          "-75.5410318208992 4.9335544228762," \
          "-73.5283895711597 6.84893487157956," \
          "-76.0167624956523 9.46366579061545," \
          "-78.0294047453918 7.54828534191209))"
startDate = "2017-04-30T00:00:00Z"
endDate = "2017-05-12T23:59:59Z"

_username = input("Please enter your username:")
__password = getpass("Please enter your password:")

sedas = SeDASAPI(_username, __password)
result_optical = sedas.search_optical(wkt, startDate, endDate, maxCloudPercent=50, minCloudPercent=25)
print(json.dumps(result_optical, sort_keys=True, indent=4, separators=(',', ': ')))
```

### Search for a SAR AOI

```python
import json
from getthestuff.sedas_api import SeDASAPI
from getpass import getpass

wkt = "POLYGON ((-78.0294047453918 7.54828534191209," \
          "-75.5410318208992 4.9335544228762," \
          "-73.5283895711597 6.84893487157956," \
          "-76.0167624956523 9.46366579061545," \
          "-78.0294047453918 7.54828534191209))"
startDate = "2017-04-30T00:00:00Z"
endDate = "2017-05-12T23:59:59Z"

_username = input("Please enter your username:")
__password = getpass("Please enter your password:")

sedas = SeDASAPI(_username, __password)
result_sar = sedas.search_sar(wkt, startDate, endDate)
print(json.dumps(result_sar, sort_keys=True, indent=4, separators=(',', ': ')))
```

### Search for a single product

```python
import json
from getthestuff.sedas_api import SeDASAPI
from getpass import getpass

_username = input("Please enter your username:")
__password = getpass("Please enter your password:")

sedas = SeDASAPI(_username, __password)
singleProduct = sedas.search_product("S1B_IW_GRDH_1SDV_20190528T105030_20190528T105055_016443_01EF3E_5E4F")
print(json.dumps(singleProduct, sort_keys=True, indent=4, separators=(',', ': ')))```
```

### Download a single product

```python
from getthestuff.sedas_api import SeDASAPI
from getpass import getpass

_username = input("Please enter your username:")
__password = getpass("Please enter your password:")

sedas = SeDASAPI(_username, __password)
singleProduct = sedas.search_product("S1B_IW_GRDH_1SDV_20190528T105030_20190528T105055_016443_01EF3E_5E4F")

sedas.download(singleProduct, "/output/path/")
```

### Bulk download many products
Note with historical request this can take a while to recover the images from the archive.
```python
from getthestuff.bulk_download import SeDASBulkDownload
from getthestuff.sedas_api import SeDASAPI
from getpass import getpass
import time

wkt = "POLYGON ((-78.0294047453918 7.54828534191209," \
          "-75.5410318208992 4.9335544228762," \
          "-73.5283895711597 6.84893487157956," \
          "-76.0167624956523 9.46366579061545," \
          "-78.0294047453918 7.54828534191209))"
startDate = "2017-04-30T00:00:00Z"
endDate = "2017-05-12T23:59:59Z"

_username = input("Please enter your username:")
__password = getpass("Please enter your password:")

sedas = SeDASAPI(_username, __password)

# Search for some images.
result_sar = sedas.search_sar(wkt, startDate, endDate)
# Create a downloader. This will spawn a number of background threads to actually do the downloading
# And waiting for historical requests.
downloader = SeDASBulkDownload(sedas, "/output/path/", parallel=3, verbose=True)

# Add the things we want to download to the queue
downloader.add(result_sar['products'])

# Wait for the downloader to be finished.
while not downloader.is_done():
    time.sleep(5)
    
# clean up the background threads.
downloader.shutdown()

```

### Docker environment

A simple docker environment is provided. This is probably not all that useful yet. 
Run the following commands from this directory:

```shell
make docker
docker run -it sedas-client:latest /bin/bash
```

This assumes you have docker installed. It will leave you in a shell which has all the tools defined in the docker file 
installed.

Extra tools required will happily be added just make a request. 