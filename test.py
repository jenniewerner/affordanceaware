# -*- coding: utf-8 -*-
"""
Yelp Fusion API code sample.

This program demonstrates the capability of the Yelp Fusion API
by using the Search API to query for businesses by a search term and location,
and the Business API to query additional information about the top result
from the search query.

Please refer to http://www.yelp.com/developers/v3/documentation for the API
documentation.

This program requires the Python requests library, which you can install via:
`pip install -r requirements.txt`.

Sample usage of the program:
`python sample.py --term="bars" --location="San Francisco, CA"`
"""
from __future__ import print_function

import argparse
import pprint
import requests
import sys

from os import environ
from yelp import Yelp

# This client code can run on Python 2.x or 3.x.  Your imports can be
# simpler if you only need one of those.
try:
    # For Python 3.0 and later
    from urllib.error import HTTPError
    from urllib.parse import quote
    from urllib.parse import urlencode
except ImportError:
    # Fall back to Python 2's urllib2 and urllib
    from urllib2 import HTTPError
    from urllib import quote
    from urllib import urlencode

# Yelp Fusion no longer uses OAuth as of December 7, 2017.
# You no longer need to provide Client ID to fetch Data
# It now uses private keys to authenticate requests (API Key)
# You can find it on
# https://www.yelp.com/developers/v3/manage_app
API_KEY = environ.get("YELP_API_KEY")

# API constants, you shouldn't have to change these.
API_HOST = 'https://api.yelp.com'
SEARCH_PATH = '/v3/businesses/search'
BUSINESS_PATH = '/v3/businesses/'  # Business ID will come after slash.

# Defaults for our simple example.
DEFAULT_TERM = 'grocery'
DEFAULT_LAT = 42.039410
DEFAULT_LNG = -87.680839
SEARCH_LIMIT = 10
SEARCH_RADIUS = 1000


def request(host, path, api_key, url_params=None):
    """Given your API_KEY, send a GET request to the API.

    Args:
        host (str): The domain host of the API.
        path (str): The path of the API after the domain.
        api_key (str): Your API Key.
        url_params (dict): An optional set of query parameters in the request.

    Returns:
        dict: The JSON response from the request.

    Raises:
        HTTPError: An error occurs from the HTTP request.
    """
    url_params = url_params or {}
    url = '{0}{1}'.format(host, quote(path.encode('utf8')))
    headers = {
        'Authorization': 'Bearer %s' % api_key,
    }

    print(u'Querying {0} ...'.format(url))
    print(url)
    print(url_params)
    response = requests.request('GET', url, headers=headers, params=url_params)
    return response.json()


def search(api_key, term, lat, lng):
    """Query the Search API by a search term and location.

    Args:
        api_key (str): Your API Key.
        term (str): The search term passed to the API.
        lat (float): latitude
        lng (float): longitude

    Returns:
        dict: The JSON response from the request.
    """
    url_params = {
        'sort_by': 'distance',
        'latitude': lat,
        'longitude': lng,
        'limit': SEARCH_LIMIT,
        'radius': SEARCH_RADIUS,
        'term': term
    }
    return request(API_HOST, SEARCH_PATH, api_key, url_params=url_params)


def get_business(api_key, business_id):
    """Query the Business API by a business ID.

    Args:
        api_key (str): Your API Key.
        business_id (str): The ID of the business to query.

    Returns:
        dict: The JSON response from the request.
    """
    business_path = BUSINESS_PATH + business_id

    return request(API_HOST, business_path, api_key)


def query_api(term, lat, lng):
    """Queries the API by the input values from the user.

    Args:
        term (str): The search term to query.
        lat (float): latitude
        lng (float): longitude
    """
    response = search(API_KEY, term, lat, lng)

    businesses = response.get('businesses')

    for b in businesses:
        print(b['id'])

    if not businesses:
        print(u'No businesses for {0} found.'.format(term))
        return

    business_id = businesses[0]['id']

    print(u'{0} businesses found, querying business info for the top result "{1}" ...'.format(len(businesses),
                                                                                              business_id))
    response = get_business(API_KEY, business_id)

    # print(u'Result for business "{0}" found:'.format(business_id))
    pprint.pprint(response, indent=2)


def main():
    parser = argparse.ArgumentParser()

    parser.add_argument('-q', '--term', dest='term', default=DEFAULT_TERM,
                        type=str, help='Search term (default: %(default)s)')
    parser.add_argument('-lat', '--lat', dest='lat',
                        default=DEFAULT_LAT, type=str,
                        help='Search lat (detfault: %(default)s)')
    parser.add_argument('-lng', '--lng', dest='lng',
                        default=DEFAULT_LNG, type=str,
                        help='Search lng (default: %(default)s)')

    input_values = parser.parse_args()

    try:
        query_api(input_values.term, input_values.lat, input_values.lng)
    except HTTPError as error:
        sys.exit(
            'Encountered HTTP error {0} on {1}:\n {2}\nAbort program.'.format(
                error.code,
                error.url,
                error.read(),
            )
        )


if __name__ == '__main__':
    main()
