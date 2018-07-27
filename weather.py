"""
This module is a class wrapper for the OpenWeatherMap API and time-based affordances.
"""
from __future__ import print_function
from __future__ import absolute_import

import requests


class Weather(object):
    """
    Manages queries to the OpenWeatherMap API (https://openweathermap.org/api) for weather affordances and computes
    additional time-based affordances.

    Attributes:
        api_key (string): API key to authenticate requests with.
    """

    def __init__(self, api_key):
        """
       Returns a Weather object with class variables initialized.

       :param api_key: string for OpenWeatherMap API Key.
       """
        # setup keys
        self.api_key = api_key

    def get_weather_at_location(self, lat, lng):
        """
        Makes a request to the weather API for the weather at the current location.

        :param lat: float latitude to center request around.
        :param lng: float longitude to center request around.
        :return: JSON response as dict from weather API for current weather at current location
        """
        # make request
        url = 'http://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={api_key}'
        resp = requests.get(url.format(latitude=str(lat), longitude=str(lng), api_key=self.api_key))

        # return if request is valid
        if resp.status_code == requests.codes.ok:
            return resp.json()

        return None

    def get_forecast_at_location(self, lat, lng):
        """
        Makes a request to the weather API for the forecast at the current location.

        :param lat: latitude, as a float
        :param lng: longitude, as a float
        :return: JSON response as dict from weather API for current forecast at current location
        """
        url = 'http://api.openweathermap.org/data/2.5/forecast?lat={latitude}&lon={longitude}&appid={api_key}'
        resp = requests.get(url.format(latitude=str(lat), longitude=str(lng), api_key=self.api_key))

        # return if request is valid
        if resp.status_code == requests.codes.ok:
            return resp.json()

        return None
