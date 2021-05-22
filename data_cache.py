import datetime
from pymongo import MongoClient, GEO2D
from geopy.distance import geodesic


class DataCache(object):
    """
    Maintains a connection to a MongoDB database used for caching location-based data,
    and a set of methods for interacting with that database.

    Attributes:
        mongo_uri: A string that tells what MongoDB to use for the location cache.
        db: DB to use.
        client: Mongo client initialized with mongo_uri.
    """

    def __init__(self, mongo_uri, db_name):
        """
        Returns a DataCache object with class variables and MongoDB client initialized.

        :param mongo_uri: A string that tells what MongoDB to use for the location cache.
        :param db_name: A string indicating DB to use.
        """
        # setup DB related attributes
        self.mongo_uri = mongo_uri
        self.client = MongoClient(self.mongo_uri)

        self.db = self.client[db_name]

    def fetch_from_cache(self, collection_name, lat, lng, distance_threshold, time_threshold):
        """
        Fetches the nearest cached location to lat, lng and returns if within self.threshold distance.

        :param collection_name: A string indicating collection to use.
        :param lat: Latitude of location, as float.
        :param lng: Longitude of location, as float.
        :param distance_threshold: A float that determine the distance in meters the nearest cache entry must be within.
        :param time_threshold: An int that specifies the longest data in the cache is valid for in minutes.
        :return: tuple of (dict, bool) where dict is cached location (or None) and bool is whether location is valid
        """
        # get the current collection
        current_collection = self.db[collection_name]

        # setup index if it doesnt already exist
        current_collection.create_index([('location', GEO2D)])

        # find nearest location
        nearest_cached_loc = current_collection.find_one({'location': {'$near': [lng, lat]}})

        # check if valid cache object is returned
        if nearest_cached_loc is not None:
            # compute distance to nearest cached object
            nearest_cached_loc_location = (nearest_cached_loc['location'][1], nearest_cached_loc['location'][0])
            dist_to_nearest = geodesic(nearest_cached_loc_location, (lat, lng)).meters

            # compute time diff between cached object and current time
            current_date = datetime.datetime.utcnow()
            time_delta_sec_to_nearest = (current_date - nearest_cached_loc['date']).total_seconds()
            time_delta_mins_to_nearest = divmod(time_delta_sec_to_nearest, 60)[0]

            print('{} -- Nearest cached location: {} meters away, {} minutes ago.'.format(collection_name,
                                                                                          dist_to_nearest,
                                                                                          time_delta_mins_to_nearest))

            # cache is valid if within distance
            if dist_to_nearest < distance_threshold:
                # return cache object iff valid AND within time threshold
                if time_delta_mins_to_nearest < time_threshold:
                    return nearest_cached_loc, True
                else:
                    return nearest_cached_loc, False

        # no valid cache object could be found
        return None, False

    def add_to_cache(self, collection_name, lat, lng, data_to_save):
        """
        Adds location to cache.

        :param collection_name: A string indicating collection to use.
        :param lat: Latitude of location, as float.
        :param lng: Longitude of location, as float.
        :param data_to_save: Data to save for location, as list
        :return: inserted id of document, if successful
        """
        # get the current collection
        current_collection = self.db[collection_name]

        # add new data to cache
        return current_collection.insert_one({
            'location': [lng, lat],  # longitude, latitude format
            'data': data_to_save,
            'date': datetime.datetime.utcnow()
        }).inserted_id

    def update_cache(self, collection_name, object_id, new_data_to_save):
        """
        Updates existing location in cache.

        :param collection_name: A string indicating collection to use.
        :param object_id: Id of object to update, as ObjectId
        :param new_data_to_save: Data to save for location, as list
        :return: inserted id of document, if successful
        """
        # get the current collection
        current_collection = self.db[collection_name]

        # update data for object_id
        return current_collection.update_one({
            '_id': object_id
        }, {
            '$set': {
                'data': new_data_to_save,
                'date': datetime.datetime.utcnow()
            }
        }, upsert=False)


if __name__ == 'main':
    pass
