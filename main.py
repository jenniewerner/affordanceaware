from __future__ import print_function
from __future__ import absolute_import

# application setup
from os import environ
from flask import Flask, jsonify
from flask_cors import CORS

# location and time imports
import datetime
from pytz import timezone, utc
from timezonefinder import TimezoneFinder

# Modules
from yelp import Yelp
from weather import Weather
from sunrise_sunset import SunriseSunset
from data_cache import DataCache

# setup Flask app
app = Flask(__name__)
cors = CORS(app, resources={r"/api": {"origins": "http://localhost:3000"}})

# setup yelp API
HARDCODED_LOCATION = [
        ({"sargent_hall_evanston": ["cafeteria"]}, (42.058813, -87.675602)),
        ({"lakefill_southtip_evanston": ["parks", "lakes"]}, (42.052460, -87.669876)),
        # ("hackerspace", (42.056929, -87.676694)),
        # ("end_of_f_wing", (42.057472, -87.67662)),
        # ("atrium", (42.057323, -87.676164)),
        # ("k_wing", (42.05745, -87.675085)),
        # ("l_wing",(42.057809, -87.67611)),
        # temporary
        # ("grocery", (42.047691, -87.679189)),
        # ("grocery", (42.047691, -87.679189)),
        # ("grocery", (42.047874, -87.679489)),
        # ("gyms", (42.061293, -87.676620)),
        # ("train_stations", (42.058623, -87.683433)),
        # ("train_stations", (42.019285, -87.673238)),
        # ("libraries", (42.058141, -87.674490)),
        # ("field", (42.058364, -87.67089)),               # lakeside field
        # ("field", (42.053160, -87.677064)),              # deering meadow, street side
        # ("field", (42.053311, -87.675788)),              # deering meadow, university side
        # ("parks", (42.053192, -87.676967)),              # deering meadow
        # ("religious_schools", (42.056168, -87.675802)),
        # ("religious_schools", (42.050438, -87.677565)),  # alice millar
        # ("gyms", (42.054259, -87.678203)),               # blom
        # ("gyms", (42.059575, -87.672667)),               # spac
        # ("gyms", (42.059612, -87.673462)),               # spac
        # ("religious_schools", (42.053232, -87.677212)),
        # ("libraries", (42.053046, -87.674814)),
        # ("libraries", (42.053046, -87.674814)),
        # ("lakes", (47.671756, -122.344640)),             # greenlake
        # ("lakes", (47.681494, -122.341121)),             # greenlake
        # ("lakes", (47.680194, -122.327946)),             # greenlake
        # ("parks", (47.680194, -122.327946)),             # greenlake
        # ("bars", (47.600759, -122.331817)),              # mccoy's
        # ("parks", (47.724032, -122.337868)),             # ingraham
        # ("parks", (42.056569, -87.677079)),              # shakespeare garden near sheridan
        # ("parks", (42.059315, -87.675995)),              # frat grass
        # ("parks", (42.052750, -87.677229)),              # deering street side again
        # ("parks", (42.053808, -87.678296)),              # foster
        # ("parks", (42.053881, -87.677290)),              # foster and sheridan
        # ("parks", (42.056257, -87.676201)),              # garrett
        # ("parks", (42.057223, -87.677239)),              # seabury
        # ("parks", (42.053893, -87.681738)),              # foster and sherman
        # ("parks", (42.055037, -87.679631)),              # library and orrington
        # ("parks", (42.057300, -87.679615))               # haven and orrington
]
# get configuration variables for hardcoded location threshold and yelp query radius
HARDCODED_LOCATION_DISTANCE_THRESHOLD = environ.get("HARDCODED_LOCATION_DISTANCE_THRESHOLD")
if HARDCODED_LOCATION_DISTANCE_THRESHOLD is None:
    # default to 60 meters
    HARDCODED_LOCATION_DISTANCE_THRESHOLD = 60.0
    print("HARDCODED_LOCATION_DISTANCE_THRESHOLD not specified. Default to {} minutes.".format(HARDCODED_LOCATION_DISTANCE_THRESHOLD))
else:
    HARDCODED_LOCATION_DISTANCE_THRESHOLD = float(HARDCODED_LOCATION_DISTANCE_THRESHOLD)


YELP_QUERY_RADIUS = environ.get("YELP_QUERY_RADIUS")
if YELP_QUERY_RADIUS is None:
    # default to 30 meters
    YELP_QUERY_RADIUS = 30.0
    print("YELP_QUERY_RADIUS not specified. Default to {} minutes.".format(YELP_QUERY_RADIUS))
else:
    YELP_QUERY_RADIUS = float(YELP_QUERY_RADIUS)

# setup Yelp API with configuration variables
YELP_API = Yelp(environ.get("YELP_API_KEY"), hardcoded_locations=HARDCODED_LOCATION)

# setup weather API
WEATHER_API = Weather(environ.get("WEATHER_KEY"))

SUNRISE_SUNSET_API = SunriseSunset()

# setup DB connection to cache
MONGODB_URI = environ.get("MONGODB_URI")
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

# get configuration variables for Weather cache
WEATHER_CACHE_DISTANCE_THRESHOLD = environ.get("WEATHER_CACHE_DISTANCE_THRESHOLD")
if WEATHER_CACHE_DISTANCE_THRESHOLD is None:
    WEATHER_CACHE_DISTANCE_THRESHOLD = 16000.0  # 16 kilometers = 10 miles
    print("WEATHER_CACHE_DISTANCE_THRESHOLD not specified. Default to {} meters.".format(WEATHER_CACHE_DISTANCE_THRESHOLD))
else:
    WEATHER_CACHE_DISTANCE_THRESHOLD = float(WEATHER_CACHE_DISTANCE_THRESHOLD)

WEATHER_CACHE_TIME_THRESHOLD = environ.get("WEATHER_CACHE_TIME_THRESHOLD")
if WEATHER_CACHE_TIME_THRESHOLD is None:
    WEATHER_CACHE_TIME_THRESHOLD = 30  # 30 minutes
    print("WEATHER_CACHE_TIME_THRESHOLD not specified. Default to {} minutes.".format(WEATHER_CACHE_TIME_THRESHOLD))
else:
    WEATHER_CACHE_TIME_THRESHOLD = float(WEATHER_CACHE_TIME_THRESHOLD)

# get configuration variables for SunriseSunset cache
SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD = environ.get("SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD")
if SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD is None:
    SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD = 100000.0   # 100km = 60 miles
    print("SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD not specified. Default to {} meters.".format(SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD))
else:
    SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD = float(SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD)

SUNRISE_SUNSET_TIME_THRESHOLD = environ.get("SUNRISE_SUNSET_TIME_THRESHOLD")
if SUNRISE_SUNSET_TIME_THRESHOLD is None:
    # 4 hours (if we cached at 11:59p yesterday, it will update with todays info at 3:59a, plenty of time before next sunrise)
    SUNRISE_SUNSET_TIME_THRESHOLD = 60 * 4
    print("SUNRISE_SUNSET_TIME_THRESHOLD not specified. Default to {} minutes.".format(SUNRISE_SUNSET_TIME_THRESHOLD))
else:
    SUNRISE_SUNSET_TIME_THRESHOLD = float(SUNRISE_SUNSET_TIME_THRESHOLD)

# initialize data cache
DATA_CACHE = DataCache(MONGODB_URI, "affordance-aware")


# routes
@app.route('/location_tags/<string:lat>/<string:lng>', methods=['GET'])
def get_location_tags(lat, lng):
    """
    Gets tags for location, as a list.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: current conditions as a list
    """
    return jsonify(get_current_conditions(float(lat), float(lng)))


@app.route('/location_keyvalues/<string:lat>/<string:lng>', methods=['GET'])
def get_location_keyvalues(lat, lng):
    """
    Gets tags for location, as a dict.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: current conditions as key-value pairs
    """
    return jsonify(get_current_conditions_as_keyvalues(float(lat), float(lng)))

@app.route('/location_weather_time_keyvalues/<string:lat>/<string:lng>', methods=['GET'])
def get_location_weather_time_keyvalues(lat, lng):
    """
    Gets tags for location, as a dict.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: current conditions as key-value pairs
    """

    return jsonify(get_weather_time_conditions_as_keyvalues(float(lat), float(lng)))

@app.route("/")
def hello():
    """
    Default route.

    :return: string of "Hello World!"
    """
    return "Hello World!"


# output formatting helper function
def get_current_conditions(lat, lng):
    """
    Gets the user's current affordance state, given a latitude/longitude, and returns as an list.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: list of weather, yelp API response, and local locations
    """
    # get weather, yelp, and any custom affordances
    current_conditions = []
    current_conditions += compute_weather_time_affordances(lat, lng)[0]  # current weather/time affordances
    current_conditions += get_categories_for_location(lat, lng)[0]       # current list of yelp conditions
    current_conditions += get_custom_affordances(current_conditions)[0]  # custom list of affordances

    # cleanup before returning
    return [YELP_API.clean_string(aff) for aff in current_conditions]

def get_current_conditions_as_keyvalues(lat, lng):
    """
    Gets the user's current affordance state, given a latitude/longitude, and returns as an dictionary.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: dict of weather, yelp API response, and local locations
    """
    # fetch data
    weather_time_affordances = compute_weather_time_affordances(lat, lng)
    yelp_affordances = get_categories_for_location(lat, lng)
    # NOTE(rlouie) 3/2/19: not using custom affordances for any experiences
    # custom_affordances = get_custom_affordances(weather_time_affordances[0] + yelp_affordances[0])

    curr_conditions = {}
    curr_conditions.update(weather_time_affordances[1]) # weather/time nested dict
    curr_conditions.update(yelp_affordances[1]) # yelp nested dict
    # NOTE(rlouie) 3/2/19: not using custom affordances for any experiences
    # curr_conditions.update(custom_affordances[1])

    # cleanup before returning
    return {YELP_API.clean_string(k): v for k, v in curr_conditions.items()}

def get_weather_time_conditions_as_keyvalues(lat, lng):
    """
    Gets the user's current affordance state, given a latitude/longitude, and returns as an dictionary.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: dict of weather, yelp API response, and local locations
    """
    curr_conditions = {}
    weather_time_affordances = compute_weather_time_affordances(float(lat), float(lng))
    curr_conditions.update(weather_time_affordances[1])

    # cleanup before returning
    return {YELP_API.clean_string(k): v for k, v in curr_conditions.items()}


def place_categories_dict_as_keyvalues(place_categories_dict):
    """
    :param place_categories_dict: [dict] {'bat_17_evanston': ['sandwiches', 'sportsbars'],
                                          'le_peep_evanston': ['breakfast']}
    :return res: [dict] {
                            'bat_17_evanston': {
                                'sandwiches': True,
                                'sportsbars': True
                             },
                             'le_peep_evanston': {
                                'breakfast': True
                             }
                        }
    """
    res = {}
    for place, category_list in place_categories_dict.items():
        nested_category_dict = {category: True for category in category_list}
        res[place] = nested_category_dict
    return res


# location helper functions
def get_categories_for_location(lat, lng):
    """
    Returns list of strings indicating the name of businesses and categories around the lat, lng

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: tuple of (list, key-value dict) of yelp response
    """
    # check cache, if not there then query from yelp
    cached_location, valid_cache_location = DATA_CACHE.fetch_from_cache('LocationCache', lat, lng,
                                                                        YELP_CACHE_DISTANCE_THRESHOLD,
                                                                        YELP_CACHE_TIME_THRESHOLD)

    # check validity of cache
    if cached_location is not None:
        if valid_cache_location:
            print("Yelp API -- VALID Cache HIT...returning cached data.")
            place_categories_dict = cached_location['data']
            return place_categories_dict, place_categories_dict_as_keyvalues(place_categories_dict)
        else:
            print("Yelp API -- EXPIRED Cache HIT...querying data from OpenWeatherMaps.")
    else:
        print("Yelp API -- Cache MISS...querying data from Yelp.")

    # get data from Yelp API
    place_categories_dict = fetch_yelp_data(lat, lng)
    print("Yelp API -- locations/categories from Yelp: {}".format(place_categories_dict))

    # add/update to cache depending on if object previously existed in cache
    if cached_location is None:
        DATA_CACHE.add_to_cache('LocationCache', lat, lng, place_categories_dict)
    else:
        DATA_CACHE.update_cache('LocationCache', cached_location['_id'], place_categories_dict)

    # return output tuple
    return place_categories_dict, place_categories_dict_as_keyvalues(place_categories_dict)


def fetch_yelp_data(lat, lng):
    """
    Returns data from Yelp as a list, given at latitude and longitude.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: list of Yelp responses, empty if nothing is returned
    """
    # query data from yelp
    categories = ['grocery', 'trainstations', 'transport', 'bars', 'climbing', 'cafeteria', 'libraries',
                  'religiousorgs', 'sports_clubs', 'fitness']
    place_categories_dict = YELP_API.fetch_all_locations(lat, lng, ','.join(categories),
                                                         distance_threshold=HARDCODED_LOCATION_DISTANCE_THRESHOLD,
                                                         radius=YELP_QUERY_RADIUS)

    #  if request returns None, return empty
    if place_categories_dict is None:
        return {}
    return place_categories_dict


def get_custom_affordances(conditions):
    """
    Adds additional affordances to conditions if a match is found.

    :param conditions: list of conditions, as returned from `get_current_conditions`
    :return: tuple of (list, key-value dict) of conditions with additional affordances, if found
    """
    custom_affordances = {
        "beaches": ["waves", "build_a_sandcastle"],
        "northwestern_university_library": ["castle"],
        "coffee": ["chair", "sit_in_a_chair"],
        "parks": ["trees", "grass", "frolick", "hug_a_tree", "pick_a_leaf"],
        "hackerspace": ["computer", "relax_in_a_chair", "surf_the_interweb"],
        "train_stations": ["train", "ride_a_train"],
        "northwestern_university_sailing_center_evanston": ["sailboat"]
    }

    found_custom_affordances = [affordance_to_add
                                for key in custom_affordances
                                for affordance_to_add in custom_affordances[key] if key in conditions]

    # return output tuple
    return found_custom_affordances, {key: True for key in found_custom_affordances}

# weather and time helper functions
def get_weather_data(lat, lng):
    """
    Fetches weather and forecast data for location from cache, if possible. Otherwise, queries API.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return: dict with keys 'weather' and 'forecast' with lists containing current weather and forecast responses.
    """
    # check cache, if not there then query from weather api
    cached_location, valid_cache_location = DATA_CACHE.fetch_from_cache('WeatherCache', lat, lng,
                                                                        WEATHER_CACHE_DISTANCE_THRESHOLD,
                                                                        WEATHER_CACHE_TIME_THRESHOLD)

    # check validity of cached location
    if cached_location is not None:
        if valid_cache_location:
            print("Weather API -- VALID Cache HIT...returning cached data.")
            weather_forecast_dict = cached_location['data']
            return weather_forecast_dict
        else:
            print("Weather API -- EXPIRED Cache HIT...querying data from OpenWeatherMaps.")
    else:
        print("Weather API -- Cache MISS...querying data from OpenWeatherMaps.")

    # query data from API
    weather_results = WEATHER_API.get_weather_at_location(lat, lng)
    forecast_results = WEATHER_API.get_forecast_at_location(lat, lng)

    if weather_results is None:
        weather_results = []

    if forecast_results is None:
        forecast_results = []

    weather_forecast_dict = {
        'weather': weather_results,
        'forecast': forecast_results
    }
    print("Weather API -- weather/forecast from OpenWeatherMaps: {}".format(weather_forecast_dict))

    # update/add to cache as needed
    if cached_location is None:
        DATA_CACHE.add_to_cache('WeatherCache', lat, lng, weather_forecast_dict)
    else:
        DATA_CACHE.update_cache('WeatherCache', cached_location['_id'], weather_forecast_dict)

    # return weather/forecast dict
    return weather_forecast_dict

# sunrise/sunset time information
def get_sunrise_sunset_data(lat, lng):
    """
    Fetches sunset/sunrise for location from cache, if possible. Otherwise, queries API.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return:  TODO(rlouie)
    """
    cached_location, valid_cache_location = DATA_CACHE.fetch_from_cache('SunriseSunsetCache', lat, lng,
                                                                        SUNRISE_SUNSET_CACHE_DISTANCE_THRESHOLD,
                                                                        SUNRISE_SUNSET_TIME_THRESHOLD)
    # check validity of cached location
    if cached_location is not None:
        if valid_cache_location:
            print("SunriseSunset API -- VALID Cache HIT...returning cached data.")
            sunrise_sunset_dict = cached_location['data']
            return sunrise_sunset_dict
        else:
            print("SunriseSunset API -- EXPIRED Cache HIT...querying data from sunrise-sunset.org/api.")
    else:
        print("Weather API -- Cache MISS...querying data from sunrise-sunset.org/api.")

    # query data from API
    sunrise_sunset_dict = SUNRISE_SUNSET_API.get_sunrise_sunset_at_location(lat, lng)

    if sunrise_sunset_dict is None:
        sunrise_sunset_dict = {}

    print("SunriseSunset API -- weather/forecast from OpenWeatherMaps: {}".format(sunrise_sunset_dict))

    # update/add to cache as needed
    if cached_location is None:
        DATA_CACHE.add_to_cache('SunriseSunsetCache', lat, lng, sunrise_sunset_dict)
    else:
        DATA_CACHE.update_cache('SunriseSunsetCache', cached_location['_id'], sunrise_sunset_dict)

    # return weather/forecast dict
    return sunrise_sunset_dict

def compute_weather_time_affordances(lat, lng):
    """
    Get the weather for current latitude and longitude, returned as a tuple.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return: tuple of (list, key-value dict) of weather for the location
    """
    # get weather, forecast, and sunrise/sunset data
    weather_forecast_dict = get_weather_data(lat, lng)
    weather_resp = weather_forecast_dict['weather']
    forecast_resp = weather_forecast_dict['forecast']
    sunrise_sunset_dict = get_sunrise_sunset_data(lat, lng)

    # create key-value output
    output_dict = {}

    # specific local time variables
    current_local = get_local_time(lat, lng)
    current_in_utc = datetime.datetime.utcnow().replace(tzinfo=utc)
    days_of_the_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_day = days_of_the_week[current_local.weekday()]
    output_dict['utc_offset'] = current_local.utcoffset().total_seconds() / 60 / 60
    output_dict['hour'] = current_local.hour
    output_dict['minute'] = current_local.minute
    output_dict[current_local.tzinfo.zone] = True  # 'America/Chicago': True
    output_dict[current_day] = True  # 'wednesday': True

    # parse weather
    if weather_resp:
        weather_features = [weather['main'] for weather in weather_resp['weather']]
        output_dict.update({weather_key: True for weather_key in weather_features})
    else:
        weather_features = []

    # get sunrise/sunset/current times
    if sunrise_sunset_dict:
        sunrise = datetime.datetime.strptime(sunrise_sunset_dict["sunrise"], '%Y-%m-%dT%H:%M:%S+00:00')
        sunset = datetime.datetime.strptime(sunrise_sunset_dict["sunset"], '%Y-%m-%dT%H:%M:%S+00:00')
        sunrise_in_utc = sunrise.replace(tzinfo=utc)
        sunset_in_utc = sunset.replace(tzinfo=utc)
        output_dict[period_of_day(current_in_utc, sunrise_in_utc, sunset_in_utc)] = True
        output_dict['sunset_time_minutes'] = sunset.minute

    if forecast_resp and sunrise_sunset_dict:
        # parse forecast
        forecast_sunset = ''

        for prediction in forecast_resp['list']:
            forecast_dt = datetime.datetime.utcfromtimestamp(prediction['dt'])
            forecast_dt = forecast_dt.replace(tzinfo=utc)

            # get only the sunset predicted weather (weather within 3 hours of sunset time)
            if abs(sunset_in_utc - forecast_dt) <= datetime.timedelta(hours=3):
                if sunset_in_utc.weekday() == forecast_dt.weekday():
                    forecast_sunset += '{}'.format(prediction["weather"][0]["main"].lower())
                    break

        output_dict['sunset_predicted_weather'] = forecast_sunset

    # return output tuple
    return weather_features + [current_day], output_dict


def period_of_day(current_in_utc, sunrise_in_utc, sunset_in_utc):
    """
    Returns if current time is sunset, sunrise, daytime, or nighttime, given time values for each in utc.

    :param current_in_utc: current time in UTC at user's location
    :param sunrise_in_utc: sunrise time in UTC at user's location
    :param sunset_in_utc: sunset time in UTC at user's location
    :return: daylight state of user, given time, as string
    """
    print('period_of_day arguments | current_in_utc: {}, sunrise_in_utc: {}, sunset_in_utc: {}'.format(current_in_utc, sunrise_in_utc, sunset_in_utc))

    if abs(sunset_in_utc - current_in_utc) <= datetime.timedelta(minutes=30):
        return "sunset"

    if abs(sunrise_in_utc - current_in_utc) <= datetime.timedelta(minutes=30):
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
    # find the current timezone
    tf = TimezoneFinder()
    tz = timezone(tf.timezone_at(lng=lng, lat=lat))

    # get the current time with timezone set to above
    return datetime.datetime.now(tz)


if __name__ == '__main__':
    app.run(debug=True, port=int(environ.get("PORT", 5000)), host='0.0.0.0')
