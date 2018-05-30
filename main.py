from __future__ import print_function
from __future__ import absolute_import

# misc imports
import datetime

# application setup
from os import environ
from flask import Flask, jsonify
from flask_cors import CORS

# location and time imports
from pytz import timezone, utc
from timezonefinder import TimezoneFinder

# APIs
from googleplaces import GooglePlaces

# Modules
from yelp import *
from location_cache import LocationCache

# setup Flask app
app = Flask(__name__)
cors = CORS(app, resources={r"/api": {"origins": "http://localhost:3000"}})

# setup google places API
google_places = GooglePlaces(environ.get("GOOGLE_KEY"))

# setup yelp API
PRIMARY_YELP_API_KEY = environ.get("PRIMARY_YELP_KEY")
SECONDARY_YELP_API_KEY = environ.get("SECONDARY_YELP_KEY")

HARDCODED_LOCATION = [
        ("cafeteria", (42.058813, -87.675602)),
        ("parks", (42.052460, -87.669876)),
        # ("hackerspace", (42.056929, -87.676694)),
        # ("end_of_f_wing", (42.057472, -87.67662)),
        # ("atrium", (42.057323, -87.676164)),
        # ("k_wing", (42.05745, -87.675085)),
        # ("l_wing",(42.057809, -87.67611)),
        ("grocery", (42.047691, -87.679189)),
        ("grocery", (42.047691, -87.679189)),
        ("grocery", (42.047874, -87.679489)),
        ("gyms", (42.061293, -87.676620)),
        ("train_stations", (42.058623, -87.683433)),
        ("train_stations", (42.019285, -87.673238)),
        ("libraries", (42.058141, -87.674490)),
        ("field", (42.058364, -87.67089)),               # lakeside field
        ("field", (42.053160, -87.677064)),              # deering meadow, street side
        ("field", (42.053311, -87.675788)),              # deering meadow, university side
        ("parks", (42.053192, -87.676967)),              # deering meadow
        ("religious_schools", (42.056168, -87.675802)),
        ("religious_schools", (42.050438, -87.677565)),  # alice millar
        ("gyms", (42.054259, -87.678203)),               # blom
        ("gyms", (42.059575, -87.672667)),               # spac
        ("gyms", (42.059612, -87.673462)),               # spac
        ("religious_schools", (42.053232, -87.677212)),
        ("libraries", (42.053046, -87.674814)),
        ("libraries", (42.053046, -87.674814)),
        ("lakes", (47.671756, -122.344640)),             # greenlake
        ("lakes", (47.681494, -122.341121)),             # greenlake
        ("lakes", (47.680194, -122.327946)),             # greenlake
        ("parks", (47.680194, -122.327946)),             # greenlake
        ("lakes", (42.052460, -87.669876)),              # lakefill
        ("bars", (47.600759, -122.331817)),              # mccoy's
        ("parks", (47.724032, -122.337868)),             # ingraham
        ("parks", (42.056569, -87.677079)),              # shakespeare garden near sheridan
        ("parks", (42.059315, -87.675995)),              # frat grass
        ("parks", (42.052750, -87.677229)),              # deering street side again
        ("parks", (42.053808, -87.678296)),              # foster
        ("parks", (42.053881, -87.677290)),              # foster and sheridan
        ("parks", (42.056257, -87.676201)),              # garrett
        ("parks", (42.057223, -87.677239)),              # seabury
        ("parks", (42.053893, -87.681738)),              # foster and sherman
        ("parks", (42.055037, -87.679631)),              # library and orrington
        ("parks", (42.057300, -87.679615))               # haven and orrington
]

YELP_API = Yelp(PRIMARY_YELP_API_KEY, hardcoded_locations=HARDCODED_LOCATION)

# get weather API key
WEATHER_API_KEY = environ.get("WEATHER_KEY")

# setup connection to location cache
MONGODB_URI = environ.get("MONGODB_URI")
if MONGODB_URI is None or MONGODB_URI == "":
    print("MONGODB_URI not specified. Falling back to localhost.")
    MONGODB_URI = "mongodb://localhost:27017/"

CACHE_THRESHOLD = environ.get("CACHE_THRESHOLD")
if CACHE_THRESHOLD is None:
    print("CACHE_THRESHOLD not specified. Falling back to 10.0 meters.")
    CACHE_THRESHOLD = 10.0
else:
    CACHE_THRESHOLD = float(CACHE_THRESHOLD)

LOCATION_CACHE = LocationCache(MONGODB_URI, "affordance-aware", "LocationCache", threshold=CACHE_THRESHOLD)


# routes
@app.route('/location_tags/<string:lat>/<string:lng>', methods=['GET'])
def get_location_tags(lat, lng):
    """
    Gets tags for location, as a list.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return:
    """
    lat = float(lat)
    lng = float(lng)
    conditions = get_current_conditions(lat, lng)
    return jsonify(conditions)


@app.route('/location_keyvalues/<string:lat>/<string:lng>', methods=['GET'])
def get_location_keyvalues(lat, lng):
    """
    Gets tags for location, as a dict.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return:
    """
    lat = float(lat)
    lng = float(lng)
    conditions = get_current_conditions_as_keyvalues(lat, lng)
    return jsonify(conditions)


@app.route("/")
def hello():
    return "Hello World!"


# helper functions
def get_categories_for_location(lat, lng):
    """
    Returns list of strings indicating the name of businesses and categories around the lat, lng

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: list of yelp response
    """
    # check cache
    cached_location = LOCATION_CACHE.fetch_from_cache(lat, lng)
    if cached_location is not None:
        print("Cache HIT...returning cached data.")
        return cached_location['yelp_info']

    print("Cache MISS...querying data from Yelp.")

    # query data from yelp
    categories = ['grocery', 'trainstations', 'transport', 'bars', 'climbing', 'cafeteria', 'libraries',
                  'religiousorgs', 'sports_clubs']
    location_categories = YELP_API.fetch_all_locations(lat, lng, ','.join(categories), distance_threshold=60, radius=50)

    print("locations/categories from yelp: {}".format(location_categories))

    # add data to cache before returning
    LOCATION_CACHE.add_to_cache(lat, lng, location_categories)

    return location_categories


def get_current_conditions(lat, lng):
    """
    Gets the user's current affordance state, given a latitude/longitude, and returns as an list.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: list of weather, yelp API response, and local locations
    """
    current_conditions = []
    current_conditions += get_weather(lat, lng)
    current_conditions += get_categories_for_location(lat, lng)
    # current_conditions += google_api(lat, lng)
    current_conditions = map(lambda x: x.lower(), list(set(current_conditions)))

    get_objects(current_conditions)
    return current_conditions


def get_current_conditions_as_keyvalues(lat, lng):
    """
    Gets the user's current affordance state, given a latitude/longitude, and returns as an dictionary.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: dict of weather, yelp API response, and local locations
    """
    curr_conditions = {}
    curr_conditions.update(get_weather_time_keyvalues(lat, lng))
    curr_conditions.update(get_categories_for_location_keyvalues(lat, lng))
    curr_conditions = {transform_name_to_variable(k): curr_conditions[k] for k in curr_conditions}
    return curr_conditions


def get_objects(conditions):
    """
    Adds additional affordances to conditions if a match is found.

    :param conditions: list of conditions, as returned from `get_current_conditions`
    :return: list of conditions with additional affordances, if found
    """
    objects = {
        "beaches": ["waves", "build_a_sandcastle"],
        "northwestern_university_library": ["castle"],
        "coffee": ["chair", "sit_in_a_chair"],
        "parks": ["trees", "grass", "frolick", "hug_a_tree", "pick_a_leaf"],
        "hackerspace": ["computer", "relax_in_a_chair", "surf_the_interweb"],
        "trainstations": ["train", "ride_a_train"],
        "northwestern_university_sailing_center": ["sailboat"]
    }

    for key in objects:
        if key in conditions:
            conditions += objects[key]
    return conditions


def make_weather_request(lat, lng):
    """
    Makes a request to the weather API for the weather at the current location.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: JSON response as dict from weather API for current weather at current location
    """
    url = "http://api.openweathermap.org/data/2.5/weather?lat=" + str(lat) + "&lon=" + str(lng) + \
          "&appid=" + WEATHER_API_KEY
    response = (requests.get(url)).json()
    return response


def make_forecast_request(lat, lng):
    """
    Makes a request to the weather API for the forecast at the current location.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: JSON response as dict from weather API for current forecast at current location
    """
    url = "http://api.openweathermap.org/data/2.5/forecast?lat=" + str(lat) + "&lon=" + str(lng) + \
          "&appid=" + WEATHER_API_KEY
    response = (requests.get(url)).json()
    return response


def period_of_day(current_in_utc, sunrise_in_utc, sunset_in_utc):
    """
    Returns if current time is sunset, sunrise, daytime, or nighttime, given time values for each in utc.

    :param current_in_utc: current time in UTC at user's location
    :param sunrise_in_utc: sunrise time in UTC at user's location
    :param sunset_in_utc: sunset time in UTC at user's location
    :return: daylight state of user, given time, as string
    """
    if abs(sunset_in_utc - current_in_utc) <= datetime.timedelta(minutes=25):
        return "sunset"

    if abs(sunrise_in_utc - current_in_utc) <= datetime.timedelta(minutes=25):
        return "sunrise"

    if sunset_in_utc > current_in_utc > sunrise_in_utc:
        return "daytime"

    if sunset_in_utc < current_in_utc or sunrise_in_utc > current_in_utc:
        return "nighttime"


def get_local_time(lat, lng):
    """
    Given a location, find the current local time in that time zone.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return: current local time
    """
    tf = TimezoneFinder()
    tz = timezone(tf.timezone_at(lng=lng, lat=lat))
    current_local = datetime.datetime.now(tz)
    return current_local


def get_weather(lat, lng):
    """
    Get the weather for current latitude and longitude, and return as list.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return: list with weather for the location
    """
    response = make_weather_request(lat, lng)
    weather = response["weather"][0]["main"]
    sunset = datetime.datetime.fromtimestamp(response["sys"]["sunset"])
    sunrise = datetime.datetime.fromtimestamp(response["sys"]["sunrise"])

    sunset_in_utc = sunset.replace(tzinfo=utc)
    sunrise_in_utc = sunrise.replace(tzinfo=utc)
    current_in_utc = datetime.datetime.now().replace(tzinfo=utc)

    return [weather, period_of_day(current_in_utc, sunrise_in_utc, sunset_in_utc)]


def get_weather_time_keyvalues(lat, lng):
    """
    Get the weather for current latitude and longitude, and return as dict.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return: dict with weather for the location
    """
    forecast_response = make_forecast_request(lat, lng)
    response = make_weather_request(lat, lng)

    weather_tags_list = [weather["main"] for weather in response['weather']]
    kv = {weather_key: True for weather_key in weather_tags_list}

    sunset = datetime.datetime.fromtimestamp(response["sys"]["sunset"])
    sunrise = datetime.datetime.fromtimestamp(response["sys"]["sunrise"])

    sunset_in_utc = sunset.replace(tzinfo=utc)
    sunrise_in_utc = sunrise.replace(tzinfo=utc)
    current_in_utc = datetime.datetime.now().replace(tzinfo=utc)
    kv[period_of_day(current_in_utc, sunrise_in_utc, sunset_in_utc)] = True

    for prediction in forecast_response["list"]:
        forecast_dt = datetime.datetime.fromtimestamp(prediction["dt"])
        forecast_dt = forecast_dt.replace(tzinfo=utc)

        if abs(sunset_in_utc - forecast_dt) <= datetime.timedelta(hours=3):
            if sunset_in_utc.weekday() == forecast_dt.weekday():
                kv["sunset_predicted_weather"] = "\"" + prediction["weather"][0]["main"].lower() + "\""
                break

    current_local = get_local_time(lat, lng)
    kv["utc_offset"] = current_local.utcoffset().total_seconds() / 60 / 60
    kv["hour"] = current_local.hour
    kv["minute"] = current_local.minute
    # kv["sunset_time"] = sunset
    kv["sunset_time_minutes"] = sunset.minute
    kv[current_local.tzinfo.zone] = True
    days_of_the_week = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday", "sunday"]
    kv[days_of_the_week[current_local.weekday()]] = True  # "wednesday": True

    return kv


def google_api(lat, lng):
    """
    Queries Google Places API for places near the latitude/longitude specified.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return: list of places found in response, minus unnecessary things
    """
    query_result = google_places.nearby_search(lat_lng={"lat": lat, "lng": lng}, radius=20)
    info = []
    ignore = []  # ['route', 'locality', 'political']
    for place in query_result.places:
        if True not in [p in ignore for p in place.types]:
            info += [place.name] + place.types

    return info


def transform_name_to_variable(category_name):
    """
    Used to get the category names to align with the variables that are created in affinder.

    :param category_name: name to reformat, as string
    :return: reformatted name
    """
    return (category_name.replace('/', '_')
            .replace(' ', '_')
            .replace('&', '_')
            .replace('\'', '_')
            .replace('(', '_')
            .replace(')', '_')
            .replace('-', '_')
            .lower())


def get_categories_for_location_keyvalues(lat, lng):
    """
    Returns key:value pairs indicating the name of businesses and categories around the lat, lng where values are True.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return: dict of Yelp locations matching term within radius of location
    """
    return {key: True for key in get_categories_for_location(lat, lng)}


if __name__ == '__main__':
    app.run(debug=True, port=int(environ.get("PORT", 5000)), host='0.0.0.0')
