from __future__ import print_function
from __future__ import absolute_import

# application setup
import requests
from os import environ
from flask import Flask, jsonify
from flask_cors import CORS

# location and time imports
import datetime
from pytz import timezone, utc
from timezonefinder import TimezoneFinder

# Modules
from yelp import Yelp
from location_cache import LocationCache

# setup Flask app
app = Flask(__name__)
cors = CORS(app, resources={r"/api": {"origins": "http://localhost:3000"}})

# setup yelp API
YELP_API_KEY = environ.get("YELP_API_KEY")

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

# setup notification interval in seconds
DEFAULT_WEATHER_INTERVAL = 0 * 60
DEFAULT_LOCATION_INTERVAL = 5 * 60
CUSTOM_INTERVALS = [
    (0, {'parks'}),
    (5 * 60, {}),
    (10 * 60, {'grocery'})
]

YELP_API = Yelp(YELP_API_KEY, hardcoded_locations=HARDCODED_LOCATION)

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
    current_conditions += get_weather_time(lat, lng)  # current weather conditions
    current_conditions += get_categories_for_location(lat, lng)  # current yelp conditions
    current_conditions += get_custom_affordances(current_conditions)  # custom affordances

    # cleanup and deduplicate before returning
    return list({current_affordance.lower() for current_affordance in current_conditions})


def get_current_conditions_as_keyvalues(lat, lng):
    """
    Gets the user's current affordance state, given a latitude/longitude, and returns as an dictionary.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: dict of weather, yelp API response, and local locations
    """
    curr_conditions = {}
    curr_conditions.update(get_weather_time(lat, lng, keyvalue=True))
    curr_conditions.update(get_categories_for_location(lat, lng, keyvalue=True))
    curr_conditions.update(get_custom_affordances(get_weather_time(lat, lng) + get_categories_for_location(lat, lng),
                           keyvalue=True))
    curr_conditions = {YELP_API.clean_string(k): v for k, v in curr_conditions.items()}

    # TODO: make each value a list where each is [time_before_execution, value]
    # curr_conditions = {k: (5, v) for k, v in curr_conditions.items()}
    return curr_conditions


# location helper functions
def get_categories_for_location(lat, lng, keyvalue=False):
    """
    Returns list of strings indicating the name of businesses and categories around the lat, lng

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :param keyvalue: optional boolean, whether to return as key-value dict
    :return: list or key-value dict of yelp response, based on keyvalue  param
    """
    output_list = []

    # check cache, if not there then query from yelp
    cached_location = LOCATION_CACHE.fetch_from_cache(lat, lng)
    if cached_location is not None:
        print("Cache HIT...returning cached data.")
        output_list = cached_location['yelp_info']
    else:
        print("Cache MISS...querying data from Yelp.")

        # query data from yelp
        categories = ['grocery', 'trainstations', 'transport', 'bars', 'climbing', 'cafeteria', 'libraries',
                      'religiousorgs', 'sports_clubs', 'fitness']
        location_categories = YELP_API.fetch_all_locations(lat, lng, ','.join(categories),
                                                           distance_threshold=60, radius=50)

        #  if request returns None, don't store in cache and output is empty list
        if location_categories is None:
            output_list = []
        else:
            print("locations/categories from yelp: {}".format(location_categories))

            # add data to cache
            LOCATION_CACHE.add_to_cache(lat, lng, location_categories)

            # set output list
            output_list = location_categories

    # return output as either list or key values
    if keyvalue:
        return {key: True for key in output_list}

    return output_list


def get_custom_affordances(conditions, keyvalue=False):
    """
    Adds additional affordances to conditions if a match is found.

    :param conditions: list of conditions, as returned from `get_current_conditions`
    :param keyvalue: optional boolean, whether to return as key-value dict
    :return: list or key-value dict of conditions with additional affordances, if found, based on keyvalue param
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

    # return list or dict based on keyvalue
    if keyvalue:
        return {key: True for key in found_custom_affordances}

    return found_custom_affordances


# weather and time-based helper functions
def get_weather_time(lat, lng, keyvalue=False):
    """
    Get the weather for current latitude and longitude, and return as list.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :param keyvalue: optional boolean, whether to return as key-value dict
    :return: list with weather for the location
    """
    # make weather request and parse response
    weather_resp = make_weather_request(lat, lng)
    weather_features = [weather['main'] for weather in weather_resp['weather']]

    # get sunrise/sunset/current times
    sunset = datetime.datetime.fromtimestamp(weather_resp['sys']['sunset'])
    sunrise = datetime.datetime.fromtimestamp(weather_resp['sys']['sunrise'])
    current_local = get_local_time(lat, lng)

    sunset_in_utc = sunset.replace(tzinfo=utc)
    sunrise_in_utc = sunrise.replace(tzinfo=utc)
    current_in_utc = datetime.datetime.now().replace(tzinfo=utc)

    days_of_the_week = ['monday', 'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday']
    current_day = days_of_the_week[current_local.weekday()]

    # make forecast request and parse response
    forecast_resp = make_forecast_request(lat, lng)
    forecast_sunset = ''

    for prediction in forecast_resp['list']:
        forecast_dt = datetime.datetime.fromtimestamp(prediction['dt'])
        forecast_dt = forecast_dt.replace(tzinfo=utc)

        # get only the sunset predicted weather (weather within 3 hours of sunset time)
        if abs(sunset_in_utc - forecast_dt) <= datetime.timedelta(hours=3):
            if sunset_in_utc.weekday() == forecast_dt.weekday():
                forecast_sunset += '{}'.format(prediction["weather"][0]["main"].lower())
                break

    # create and return dict if keyvalue
    if keyvalue:
        output_dict = {}

        # weather, forecast, and time of day
        output_dict.update({weather_key: True for weather_key in weather_features})
        output_dict['sunset_predicted_weather'] = forecast_sunset
        output_dict[period_of_day(current_in_utc, sunrise_in_utc, sunset_in_utc)] = True

        # specific time variables
        output_dict['utc_offset'] = current_local.utcoffset().total_seconds() / 60 / 60
        output_dict['hour'] = current_local.hour
        output_dict['minute'] = current_local.minute
        output_dict['sunset_time_minutes'] = sunset.minute
        output_dict[current_local.tzinfo.zone] = True  # 'America/Chicago': True
        output_dict[current_day] = True  # 'wednesday': True

        return output_dict

    # return list, containing only current weather features and current day
    return weather_features + [current_day]


def make_weather_request(lat, lng):
    """
    Makes a request to the weather API for the weather at the current location.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: JSON response as dict from weather API for current weather at current location
    """
    url = 'http://api.openweathermap.org/data/2.5/weather?lat={}&lon={}&appid={}'.format(str(lat),
                                                                                         str(lng),
                                                                                         WEATHER_API_KEY)
    return requests.get(url).json()


def make_forecast_request(lat, lng):
    """
    Makes a request to the weather API for the forecast at the current location.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: JSON response as dict from weather API for current forecast at current location
    """
    url = 'http://api.openweathermap.org/data/2.5/forecast?lat={}&lon={}&appid={}'.format(str(lat),
                                                                                          str(lng),
                                                                                          WEATHER_API_KEY)
    return requests.get(url).json()


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
    # find the current timezone
    tf = TimezoneFinder()
    tz = timezone(tf.timezone_at(lng=lng, lat=lat))

    # get the current time with timezone set to above
    return datetime.datetime.now(tz)


if __name__ == '__main__':
    app.run(debug=True, port=int(environ.get("PORT", 5000)), host='0.0.0.0')
