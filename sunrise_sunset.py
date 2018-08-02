"""
This module is a class wrapper for the sunrise-sunset API
"""
from __future__ import print_function
from __future__ import absolute_import

import requests


class SunriseSunset(object):
    """
    Manages queries to the sunrise sunset API (https://sunrise-sunset.org/api) and computes
    additional time-based affordances on top of this information.
    """

    def __init__(self):
        """
        Returns a SunriseSunset object with class variables initialized.
        """
        pass

    def get_sunrise_sunset_at_location(self, lat, lng):
        """
        Makes a request to the weather API for the weather at the current location.

        :param lat: float latitude to center request around.
        :param lng: float longitude to center request around.
        :return: JSON response "results" object from sunrise sunset API for today's sunrise and sunset at current location
        """
        # make request
        url = f'https://api.sunrise-sunset.org/json?lat={lat}&lng={lng}&formatted=0'
        resp = requests.get(url)

        # return if request is valid
        if resp.status_code == requests.codes.ok:
            return resp.json()['results']

        return None
