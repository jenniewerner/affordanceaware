"""
This module is a class wrapper for the Yelp API.
"""
from __future__ import print_function
from __future__ import absolute_import

import requests
from geopy.distance import vincenty


class Yelp(object):
    """
    Manages queries to the Yelp API (https://www.yelp.com/developers/documentation/v3)

    Attributes:
        header (dict): header for querying using yelp API key.
        hardcoded_locations (list): tuples of (location string, (latitude, longitude)) hardcoded locations to match on.
    """

    def __init__(self, api_key, hardcoded_locations=None):
        """
        Returns a Yelp object with class variables initialized.

        :param api_key: string for Yelp API Key.
        :param hardcoded_locations: list of categories and locations to add that are not included in Yelp.
        """
        # setup keys
        self.header = self.generate_request_header(api_key)

        # setup hardcoded locations
        if hardcoded_locations is None:
            hardcoded_locations = []

        self.hardcoded_locations = hardcoded_locations

    @staticmethod
    def generate_request_header(key):
        """
        Generates a request header given an API key.

        :param key: string API key.
        :return: dict header for request.
        """
        return {
           'Authorization': 'Bearer {}'.format(key),
           'content-type': 'application/x-www-form-urlencoded; charset=utf-8',
           'User-Agent': 'Mdx/3.8 (iPhone; iOS 10.2; Scale/3.00)'
        }

    @staticmethod
    def yelp_search(headers, lat, lng, radius=30, limit=50, term='', categories=''):
        """
        Queries Yelp with the given parameters.

        :param headers: dict header to use to send the request.
        :param lat: float latitude to center request around.
        :param lng: float longitude to center request around.
        :param radius: optional int radius to determine area around lat, lng to query for
        :param limit: optional into specifying number of location to return in a query. max is 50.
        :param term: optional string to search for. '' returns everything.
        :param categories: optional string with comma separated categories to search for (ex. 'trainstations,grocery)
            List of all categories: https://www.yelp.com/developers/documentation/v3/all_category_list
        :return: response object
        """
        params = {
            'latitude': lat,
            'longitude': lng,
            'radius': radius,
            'limit': limit
        }

        # add optional parameters
        if term != '':
            params['term'] = term

        if categories != '':
            params['categories'] = categories

        # make and return request
        return requests.get('https://api.yelp.com/v3/businesses/search', headers=headers, params=params)

    @staticmethod
    def clean_string(target_string):
        """
        Reformat string with target characters replaced with _ so that affinder can recognize them.

        :param target_string: string to reformat
        :return: reformatted name
        """
        return (target_string.replace('/', '_')
                .replace(' ', '_')
                .replace('&', '_')
                .replace('\'', '_')
                .replace('(', '_')
                .replace(')', '_')
                .replace('-', '_')
                .lower())

    def fetch_hardcoded_locations(self, lat, lng, distance_threshold=60):
        """
        Checks and returns categories for locations that are near hardcoded locations, if within distance_threshold.

        :param lat: float latitude of current location.
        :param lng: float longitude of current location.
        :param distance_threshold: optional float for how close lat, lng must be to hardcoded location
        :return:
        """
        nearby_hardcoded_place_cats = {}

        # TODO(rlouie): hardcoded_locations should look like [..., ({"placename": [affordance]}, (lat,lng)), ...]
        for location in self.hardcoded_locations:
            place_category_dict = location[0]
            curr_location_coords = location[1]

            # add location if within distance_threshold
            dist = vincenty(curr_location_coords, (lat, lng)).meters
            if dist < distance_threshold:
                nearby_hardcoded_place_cats.update(place_category_dict)

        return nearby_hardcoded_place_cats

    def fetch_yelp_locations(self, lat, lng, categories, radius=30):
        """
        Fetch yelp categories and locations, given a lat and lng location.

        :param lat: float latitude to center request around.
        :param lng: float longitude to center request around.
        :param categories: optional string with comma separated categories to search for (ex. 'trainstations,grocery)
            List of all categories: https://www.yelp.com/developers/documentation/v3/all_category_list
        :param distance_threshold: optional float for how close lat, lng must be to hardcoded location
        :param radius: optional int radius to determine area around lat, lng to query for.
        :return: categories and locations, cleaned using clean_string, if responses were successful. None otherwise.
        """
        # attempt to make yelp request
        yelp_generic_resp = self.yelp_search(self.header, lat, lng,
                                             radius=radius, limit=50, term='', categories='')
        yelp_specific_resp = self.yelp_search(self.header, lat, lng,
                                              radius=radius, limit=50, term='', categories=categories)

        # if either response failed, return None
        if yelp_generic_resp.status_code != requests.codes.ok or yelp_specific_resp.status_code != requests.codes.ok:
            print("Yelp Generic Response: \n {}".format(yelp_generic_resp.text))
            print("Yelp Specific Response: \n {}".format(yelp_specific_resp.text))
            raise RuntimeError('Yelp API endpoint returned invalid responses (see above)')

        # create yelp output
        yelp_businesses = yelp_generic_resp.json()['businesses'] + yelp_specific_resp.json()['businesses']
        place_category_dict = {}

        for business in yelp_businesses:
            # check if distance is within radius
            # note: double check since query radius also does this?
            curr_dist = business['distance']

            if not curr_dist <= radius:
                continue

            curr_business_name = self.clean_string(business['alias'])
            curr_business_categories = [self.clean_string(category['alias']) for category in business['categories']]

            print("adding: {} at distance: {} from user".format(curr_business_name, curr_dist))
            place_category_dict[curr_business_name] = curr_business_categories

        return place_category_dict

    def fetch_all_locations(self, lat, lng, categories, distance_threshold=60, radius=30):
        """
        Fetch all categories and locations, including hardcoded, given a lat and lng location.

        :param lat: float latitude to center request around.
        :param lng: float longitude to center request around.
        :param categories: optional string with comma separated categories to search for (ex. 'trainstations,grocery)
            List of all categories: https://www.yelp.com/developers/documentation/v3/all_category_list
        :param distance_threshold: optional float for how close lat, lng must be to hardcoded location
        :param radius: optional int radius to determine area around lat, lng to query for.
        :return: categories and locations, cleaned using clean_string, if responses were successful. None otherwise.
        """
        yelp_place_category_dict = self.fetch_yelp_locations(lat, lng, categories=categories, radius=radius)

        # get hardcoded categories
        hardcoded_place_category_dict = self.fetch_hardcoded_locations(lat, lng, distance_threshold=distance_threshold)

        # combine and return
        yelp_place_category_dict.update(hardcoded_place_category_dict)
        return yelp_place_category_dict
