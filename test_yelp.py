"""From root of project, call
python -m unittest test_yelp

Run this in python 3.7, there's wonky things between how str vs unicode is handled in py2 vs py3
"""
import unittest
from os import environ

from yelp import Yelp

HARDCODED_LOCATION = [
        ({"sargent_hall_evanston": ["cafeteria"]}, (42.058813, -87.675602)),
        ({"lakefill_southtip_evanston": ["parks", "lakes"]}, (42.052460, -87.669876))
]
YELP_API = Yelp(environ.get("YELP_API_KEY"), hardcoded_locations=HARDCODED_LOCATION)


class TestYelpMethods(unittest.TestCase):

    def test_fetch_hardcoded_locations_one_retrieved(self):
        """return looks like
        {'sargent_hall_evanston': {'categories': ['cafeteria'], 'distance': 30.0} }
        """
        place_category_dict = YELP_API.fetch_hardcoded_locations(42.058813, -87.675602, 60.0)
        self.assertEqual(type(place_category_dict), dict)

        text_type = str # starts as string in hardcoded
        self.assertEqual(len(place_category_dict), 1)
        for place, nested_place_metadata in place_category_dict.items():
            self.assertEqual(type(place), text_type)
            self.assertEqual(type(nested_place_metadata), dict)
            self.assertIn('categories', nested_place_metadata)
            self.assertIn('distance', nested_place_metadata)
            category_list = nested_place_metadata['categories']
            self.assertEqual(type(category_list), list)
            category = category_list[0]
            self.assertEqual(type(category), text_type)
            print(place_category_dict)

    def test_fetch_hardcoded_locations_many_retrieved(self):
        """return looks like
        {'lakefill_southtip_evanston': {'categories': ['parks', 'lakes'], 'distance': 56.0},
         'sargent_hall_evanston': {'categories': ['cafeteria'], 'distance': 100.0}
        """
        place_category_dict = YELP_API.fetch_hardcoded_locations(42.058813, -87.675602, 10000)
        self.assertEqual(type(place_category_dict), dict)

        text_type = str # starts as string in hardcoded
        for place, nested_place_metadata in place_category_dict.items():
            self.assertEqual(type(place), text_type)
            self.assertEqual(type(nested_place_metadata), dict)
            self.assertIn('categories', nested_place_metadata)
            self.assertIn('distance', nested_place_metadata)
            category_list = nested_place_metadata['categories']
            self.assertEqual(type(category_list), list)
            category = category_list[0]
            self.assertEqual(type(category), text_type)
        print(place_category_dict)

    def test_fetch_yelp_locations(self):
        """return looks like
        {'bat_17_evanston': {'categories': ['sandwiches', 'sportsbars'], 'distance': 17.0},
         'le_peep_evanston': {'categories': ['breakfast'], 'distance': 30.0}}
        """
        categories = ['grocery', 'trainstations', 'transport', 'bars', 'climbing', 'cafeteria', 'libraries',
                      'religiousorgs', 'sports_clubs', 'fitness']
        place_category_dict = YELP_API.fetch_yelp_locations(
            lat=42.048735, lng=-87.683187, categories=categories, radius=30)
        print(place_category_dict)
        for place, nested_place_metadata in place_category_dict.items():
            self.assertTrue(isinstance(place, str) or isinstance(place, unicode))
            self.assertEqual(type(nested_place_metadata), dict)
            self.assertIn('categories', nested_place_metadata)
            self.assertIn('distance', nested_place_metadata)
            category_list = nested_place_metadata['categories']

            self.assertEqual(type(category_list), list)
            category = category_list[0]
            self.assertTrue(isinstance(category, str) or isinstance(category, unicode))
        print(place_category_dict)

    def test_fetch_all_locations(self):
        categories = ['grocery', 'trainstations', 'transport', 'bars', 'climbing', 'cafeteria', 'libraries',
                      'religiousorgs', 'sports_clubs', 'fitness']
        place_category_dict = YELP_API.fetch_all_locations(
            lat=42.048735, lng=-87.683187, categories=categories, distance_threshold=10000, radius=30)
        print(place_category_dict)
        for place, nested_place_metadata in place_category_dict.items():
            self.assertTrue(isinstance(place, str) or isinstance(place, unicode))
            self.assertEqual(type(nested_place_metadata), dict)
            self.assertIn('categories', nested_place_metadata)
            self.assertIn('distance', nested_place_metadata)
            category_list = nested_place_metadata['categories']
            self.assertEqual(type(category_list), list)
            category = category_list[0]
            self.assertTrue(isinstance(category, str) or isinstance(category, unicode))
        print(place_category_dict)


    def test_clean_string(self):
        # as a static method
        self.assertEqual(Yelp.clean_string('Vietnamese'), 'vietnamese')
        self.assertEqual(Yelp.clean_string('ATV Rentals/Tours'), 'atv_rentals_tours')
        self.assertEqual(Yelp.clean_string('Hunting & Fishing Supplies'), 'hunting___fishing_supplies')
        self.assertEqual(Yelp.clean_string("May's Vietnamese Restaurant"), 'may_s_vietnamese_restaurant')

        # as instance method
        self.assertEqual(YELP_API.clean_string('Vietnamese'), 'vietnamese')
        self.assertEqual(YELP_API.clean_string('ATV Rentals/Tours'), 'atv_rentals_tours')
        self.assertEqual(YELP_API.clean_string('Hunting & Fishing Supplies'), 'hunting___fishing_supplies')
        self.assertEqual(YELP_API.clean_string("May's Vietnamese Restaurant"), 'may_s_vietnamese_restaurant')
