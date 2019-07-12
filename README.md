# sedas_pyapi

A small collection of useful functions to get data from SeDAS. Works with the API documented [here](https://geobrowser.satapps.org/docs/index.html)

Requires python 3+ has been tested with 3.7

## Installing

The project is available in PyPI. Just a pip install away.

```bash
pip install sedas_pyapi
```

If you want to build manually we will be providing a contributing guide soon which will include information about 
building and testing the project.

## Usage

Create an instance of `sedas_pyapi.sedas_api.SeDASAPI` passing in your username and password.

Then call `search_optical`, `search_sar` or `search_product` to find the details of a product.

Once you have a list of things you want to download you can use the `sedas_pyapi.bulk_download.SeDASBulkDownload` to 
download all of them. There are also download methods on the `SeDASAPI` if you need to do something a bit different.

Due to the way the SeDAS system works sometimes when you do a search you will not get a download url in the result 
object. If this happens it means that the data is available but in the long term archive (lta) and must be requested 
first. Use the `request` and `is_request_ready` methods to make a request and then wait for it to be fulfilled. If you 
use the `SeDASBulkDownload` this will take care of LTA requests for you.

For more details see the examples below

## Examples

### Creating a client

```python
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

# This is a suggestion for how to get your username and password
username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
```

The SeDASAPI object can then be used to access the rest of the api.

### Search for an optical AOI with cloud cover filters

```python
import json
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

wkt = "POLYGON ((-1.3295 51.5881," \
          "-1.3013 51.5872," \
          "-1.3020 51.5621," \
          "-1.3300 51.5622," \
          "-1.3295 51.5881))"
startDate = "2019-04-30T00:00:00Z"
endDate = "2019-05-12T23:59:59Z"

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
result_optical = sedas.search_optical(wkt, startDate, endDate, maxCloudPercent=50)
print(json.dumps(result_optical, sort_keys=True, indent=4, separators=(',', ': ')))
```

Returns a SeDAS search result object. [See more](https://geobrowser.satapps.org/docs/json_SearchResponse.html)

### Search for a SAR AOI

```python
import json
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

wkt = "POLYGON ((-1.3295 51.5881," \
          "-1.3013 51.5872," \
          "-1.3020 51.5621," \
          "-1.3300 51.5622," \
          "-1.3295 51.5881))"
startDate = "2019-04-30T00:00:00Z"
endDate = "2019-05-12T23:59:59Z"

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
result_sar = sedas.search_sar(wkt, startDate, endDate)
print(json.dumps(result_sar, sort_keys=True, indent=4, separators=(',', ': ')))
```

Returns a SeDAS search result object. [See more](https://geobrowser.satapps.org/docs/json_SearchResponse.html)

### List the source groups available to the user

```python
import json
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
result_groups = sedas.list_sensor_groups()
print(json.dumps(result_groups, sort_keys=True, indent=4, separators=(',', ': ')))

groups = []
for i in range(0, len(result_groups)):
    groups.append(result_groups[i]['name'])

print(f"Available groups are: {', '.join(groups)}")
```

Returns a list of SeDAS source group objects. [See more](https://geobrowser.satapps.org/docs/json_SourceGroup.html)

### List the satellites available to the user

```python
import json
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
result_sats = sedas.list_satellites()
print(json.dumps(result_sats, sort_keys=True, indent=4, separators=(',', ': ')))

satellites = []
for i in range(0, len(result_sats)):
    satellites.append(result_sats[i]['name'])

print(f"Available satellites are: {', '.join(satellites)}")
```

Returns a list of SeDAS satellite objects. [See more](https://geobrowser.satapps.org/docs/json_Satellite.html)

### Filtering on a group of sources
Use sedas.list_sensor_groups to get the list of source groups available for a user ([see above](#List-the-source-groups-available-to-the-user)).

```python
import json
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

wkt = "POLYGON ((-1.3295 51.5881," \
          "-1.3013 51.5872," \
          "-1.3020 51.5621," \
          "-1.3300 51.5622," \
          "-1.3295 51.5881))"
startDate = "2019-04-30T00:00:00Z"
endDate = "2019-05-12T23:59:59Z"

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
result_optical = sedas.search_optical(wkt, startDate, endDate, source_group="S2")
print(json.dumps(result_optical, sort_keys=True, indent=4, separators=(',', ': ')))
```

### Filtering on a specific satellite
Use sedas.list_satellites to get the list of satellites available for a user ([see above](#List-the-satellites-available-to-the-user)).

```python
import json
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

wkt = "POLYGON ((-1.3295 51.5881," \
          "-1.3013 51.5872," \
          "-1.3020 51.5621," \
          "-1.3300 51.5622," \
          "-1.3295 51.5881))"
startDate = "2019-04-30T00:00:00Z"
endDate = "2019-05-12T23:59:59Z"

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
result_sar = sedas.search_sar(wkt, startDate, endDate, satellite_name="Sentinel-1A")
print(json.dumps(result_sar, sort_keys=True, indent=4, separators=(',', ': ')))
```

### Search for a single product

```python
import json
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
singleProduct = sedas.search_product("S1B_IW_GRDH_1SDV_20190528T105030_20190528T105055_016443_01EF3E_5E4F")
print(json.dumps(singleProduct, sort_keys=True, indent=4, separators=(',', ': ')))
```

This returns an array containing SeDAS products. [See more](https://geobrowser.satapps.org/docs/json_Product.html)

### Download a single product

```python
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)
singleProduct = sedas.search_product("S1B_IW_GRDH_1SDV_20190528T105030_20190528T105055_016443_01EF3E_5E4F")

sedas.download(singleProduct[0], "/output/path/S1B_IW_GRDH_1SDV_20190528T105030_20190528T105055_016443_01EF3E_5E4F.zip")
```

### Bulk download many products
Note with historical request this can take a while to recover the images from the archive.
```python
from sedas_pyapi.bulk_download import SeDASBulkDownload
from sedas_pyapi.sedas_api import SeDASAPI
from getpass import getpass
import time

wkt = "POLYGON ((-1.3295 51.5881," \
          "-1.3013 51.5872," \
          "-1.3020 51.5621," \
          "-1.3300 51.5622," \
          "-1.3295 51.5881))"
startDate = "2019-04-30T00:00:00Z"
endDate = "2019-05-12T23:59:59Z"

username = input("Please enter your username:")
password = getpass("Please enter your password:")

sedas = SeDASAPI(username, password)

# Search for some images.
result_sar = sedas.search_sar(wkt, startDate, endDate, sarProductType="SLC")
# Create a downloader. This will spawn a number of background threads to actually do the downloading and waiting for 
# the long term archive requests.
downloader = SeDASBulkDownload(sedas, "/output/path/", parallel=3)

# Add the things we want to download to the queue
downloader.add(result_sar['products'])

# Wait for the downloader to be finished.
while not downloader.is_done():
    time.sleep(5)
    
# clean up the background threads.
downloader.shutdown()

```