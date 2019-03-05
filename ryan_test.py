from os import environ

from data_cache import DataCache

# setup DB connection to cache
MONGODB_URI = "mongodb://collective-experience:st3lla@ds241039.mlab.com:41039/affordance-aware"
if MONGODB_URI is None or MONGODB_URI == "":
    print("MONGODB_URI not specified. Default to localhost.")
    MONGODB_URI = "mongodb://localhost:27017/"

# get configuration variables for Yelp cache
YELP_CACHE_DISTANCE_THRESHOLD = environ.get("YELP_CACHE_DISTANCE_THRESHOLD")
if YELP_CACHE_DISTANCE_THRESHOLD is None:
    YELP_CACHE_DISTANCE_THRESHOLD = 10.0
    print("YELP_CACHE_DISTANCE_THRESHOLD not specified. Default to {} meters.".format(YELP_CACHE_DISTANCE_THRESHOLD))
else:
    YELP_CACHE_DISTANCE_THRESHOLD = float(YELP_CACHE_DISTANCE_THRESHOLD)

YELP_CACHE_TIME_THRESHOLD = environ.get("YELP_CACHE_TIME_THRESHOLD")
if YELP_CACHE_TIME_THRESHOLD is None:
    YELP_CACHE_TIME_THRESHOLD = 10080  # 1 week
    print("YELP_CACHE_TIME_THRESHOLD not specified. Default to {} minutes.".format(YELP_CACHE_TIME_THRESHOLD))
else:
    YELP_CACHE_TIME_THRESHOLD = float(YELP_CACHE_TIME_THRESHOLD)

YELP_CACHE = DataCache(MONGODB_URI, "affordance-aware", "LocationCache",
                       distance_threshold=YELP_CACHE_DISTANCE_THRESHOLD,
                       time_threshold=YELP_CACHE_TIME_THRESHOLD)

lat = 41.996751725307796
lng = -87.6555914343727
# check cache, if not there then query from yelp
cached_location, valid_cache_location = YELP_CACHE.fetch_from_cache(lat, lng)

print("cached_location", cached_location)

# check validity of cache
if cached_location is not None:
    if valid_cache_location:
        print("Yelp API -- VALID Cache HIT...returning cached data.")
        location_categories = cached_location['data']
        print("Location Categories: ", location_categories)
    else:
        print("Yelp API -- EXPIRED Cache HIT...querying data from OpenWeatherMaps.")
else:
    print("Yelp API -- Cache MISS...querying data from Yelp.")


