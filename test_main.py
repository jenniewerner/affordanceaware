"""From root of project, call
python -m unittest test_main


"""
import unittest
from main import (
    get_weather_time_conditions_as_keyvalues,
    get_current_conditions_as_keyvalues
)

BAT17 = {'lat': 42.048735, 'lng': -87.683187}

class TestEndPointHelpers(unittest.TestCase):

    def test_get_weather_time_conditions_as_keyvalues(self):
        """
        0.0.0.0:5000/location_weather_time_keyvalues/42.048735/-87.683187
        """
        weather_time_dict = get_weather_time_conditions_as_keyvalues(BAT17['lat'], BAT17['lng'])
        print("location_weather_time_keyvalues:\n {}".format(weather_time_dict))
        self.assertNotIn('bat_17_evanston', weather_time_dict)

    def test_get_current_conditions_as_keyvalues(self):
        """
        0.0.0.0:5000/location_keyvalues/42.048735/-87.683187
        """
        current_conditions = get_current_conditions_as_keyvalues(BAT17['lat'], BAT17['lng'])
        print("location_keyvalues:\n {}".format(current_conditions))
        self.assertIn('bat_17_evanston', current_conditions)

