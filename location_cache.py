import datetime
from pymongo import MongoClient, GEO2D
from geopy.distance import vincenty


class LocationCache(object):
    """
    Maintains a connection to a location cache database, and a set of methods for interacting with that database.

    Attributes:
        mongo_uri: A string that tells what MongoDB to use for the location cache.
        db: DB to use.
        collection: Collection within DB where location data is stored.
        threshold: A float that the nearest cache hit must be within.
        client: Mongo client initialized with mongo_uri.
    """

    def __init__(self, mongo_uri, db_name, collection_name, threshold=10.0):
        """
        Returns a LocationCache object with class variables and mongo client initialized.

        :param mongo_uri: A string that tells what MongoDB to use for the location cache.
        :param db_name: A string indicating DB to use.
        :param collection_name: A string indicating collection to use.
        :param threshold: A float that determine the distance the nearest cache entry must be within to hit, in meters.
        """
        # setup DB related attributes
        self.mongo_uri = mongo_uri
        self.client = MongoClient(self.mongo_uri)

        self.db = self.client[db_name]
        self.collection = self.db[collection_name]

        # setup any other variables
        self.threshold = threshold

        print('LocationCache initialized.')

    def fetch_from_cache(self, lat, lng):
        """
        Fetches the nearest cached location to lat, lng and returns if within self.threshold distance.

        :param lat: Latitude of location, as float.
        :param lng: Longitude of location, as float.
        :return: cached location as dict, or None
        """
        # setup index if it doesnt already exist
        self.collection.create_index([("location", GEO2D)])

        # find nearest location
        nearest_cached_loc = self.collection.find_one({'location': {'$near': [lng, lat]}})

        # if below threshold distance, return data. otherwise, return None
        if nearest_cached_loc is not None:
            nearest_cached_loc_location = (nearest_cached_loc['location'][1], nearest_cached_loc['location'][0])
            dist_to_nearest = vincenty(nearest_cached_loc_location, (lat, lng)).meters
            print("Distance to nearest cached location: {}".format(dist_to_nearest))

            if dist_to_nearest < self.threshold:
                return nearest_cached_loc
        return None

    def add_to_cache(self, lat, lng, yelp_location_info):
        """
        Adds location to cache.

        :param lat: Latitude of location, as float.
        :param lng: Longitude of location, as float.
        :param yelp_location_info: Information pulled from yelp for location, as list
        :return: inserted id of document, if successful
        """
        return self.collection.insert_one({
            'location': [lng, lat],  # longitude, latitude format
            'yelp_info': yelp_location_info,
            'date': datetime.datetime.utcnow()
        }).inserted_id


if __name__ == 'main':
    pass
