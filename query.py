import os
import shutil
from urllib.request import Request, urlopen
from urllib.error import HTTPError
import json


def sedas_login(_username, _password):
    """
    Log into the sedas platform.

    :param _username: user to connect with
    :param _password: password for the user
    :return: access token if login was successful.
    """
    url = "https://geobrowser.satapps.org/api/authentication"
    data = {'username': _username, 'password': _password}

    req = Request(url, json.dumps(data).encode(), headers={"Content-Type": "application/json"})
    return json.load(urlopen(req))['token']


def sedas_search(_token, _sensor, _wkt, _start_date, _end_date, **_filters):
    """
    search the sedas system for the given parameters
    :param _token: login token. See the sedas_login function
    :param _sensor: the type of sensor to query one of 'All', 'Optical', or 'SAR'
    :param _wkt: wkt formatted aoi
    :param _start_date: start date to look for
    :param _end_date: end date to look for
    :param _filters: other parameters
    :return: list of search results
    """
    url = "https://geobrowser.satapps.org/api/search"
    query = {
        'sensorFilters': {"type": _sensor},
        'filters': _filters,
        'aoiWKT': _wkt,
        'start': _start_date,
        'stop': _end_date
    }
    headers = {"Content-Type": "application/json", "Authorization": "Token " + _token}

    req = Request(url, json.dumps(query).encode(), headers=headers)
    try:
        resp = urlopen(req)
        return json.load(resp)
    except HTTPError as e:
        print(e)
        print(e.read().decode())
        raise e


def sedas_download(_token, _product, _output_path):
    """
    download a product from sedas
    :param _token: login token. See the sedas_login function
    :param _product: product dictionary from a search
    :param _output_path: where to put the output file
    :return: None
    """

    url = _product['downloadUrl']
    if not url:
        raise AttributeError("no download url defined for product")
    headers = {"Content-Type": "application/json", "Authorization": "Token " + _token}
    req = Request(url, headers=headers)
    with urlopen(req) as resp:
        with open(_output_path, "+wb") as f:
            shutil.copyfileobj(resp, f)


if __name__ == '__main__':
    wkt = "POLYGON ((-78.0294047453918 7.54828534191209,-75.5410318208992 4.9335544228762,-73.5283895711597 6.84893487157956,-76.0167624956523 9.46366579061545,-78.0294047453918 7.54828534191209))"
    startDate = "2019-04-30T00:00:00Z"
    endDate = "2019-05-30T23:59:59Z"

    username = "wil.selwood@sa.catapult.org.uk"
    password = ""
    output_path = "/tmp/"
    token = sedas_login(username, password)
    print(token)
    result = sedas_search(token, "SAR", wkt, startDate, endDate)
    print(json.dumps(result))

    for product in result['products']:
        o = os.path.join(output_path, product['supplierId'] + ".zip")
        print(f"downloading {product['supplierId']} to {o}")
        sedas_download(token, product, o)
