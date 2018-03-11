from __future__ import print_function

import datetime
from os import environ
from multiprocessing import Pool, cpu_count
from multiprocessing.dummy import Pool as ThreadPool

import requests
from flask import Flask, jsonify
from flask_cors import CORS

# location and time imports
from pytz import timezone, utc
from timezonefinder import TimezoneFinder
from geopy.distance import vincenty

# APIs
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from googleplaces import GooglePlaces, types, lang

# setup Flask app
app = Flask(__name__)
cors = CORS(app, resources={r"/api": {"origins": "http://localhost:3000"}})

# setup google places API
google_places = GooglePlaces(environ.get("GOOGLE_KEY"))

# setup yelp API
yelp_auth = auth = Oauth1Authenticator(
    consumer_key=environ.get("YELP_KEY"),
    consumer_secret=environ.get("YELP_CSECRET"),
    token=environ.get("YELP_TOKEN"),
    token_secret=environ.get("YELP_TSECRET")
)

yelp_client = Client(yelp_auth)

# get weather API key
WEATHER_API_KEY = environ.get("WEATHER_KEY")

# setup firebase
firebase_config = {
    "apiKey": environ.get("FIREBASE_KEY"),
    "authDomain": environ.get("FIREBASE_NAME") + ".firebaseapp.com",
    "databaseURL": "https://" + environ.get("FIREBASE_NAME") + ".firebaseio.com",
    "storageBucket": environ.get("FIREBASE_NAME") + ".appspot.com"
}

# check number of available CPUs
RUN_PARALLEL = True
print('CPU Count: {}, RUN_PARALLEL: {}'.format(cpu_count(), str(RUN_PARALLEL)))


# routes
@app.route('/conditions/<string:lat>/<string:lng>', methods=['GET'])
def get_conditions(lat, lng):
    return []


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


@app.route('/search/<string:cat>', methods=['GET'])
def get_search(cat):
    """
    Searches for cat in Yelp.

    :param cat: category to search for, as string
    :return:
    """
    params = {
        "term": cat,
        "radius_filter": 500,
        # "limit": 20,
        "sort": 1,  # sort by distance
    }

    resp = yelp_client.search_by_coordinates(42.046876, -87.679532, **params)
    info = []
    if not resp.businesses:
        return []
    for b in resp.businesses:
        name = b.name
        name = name.replace(" ", "_")
        categories = [c[1] for c in b.categories]
        info = info + [name, categories]

    return jsonify(info)


@app.route('/local_testing/<string:lat>/<string:lng>', methods=['GET'])
def local_testing_spots(lat, lng):
    """
    Search for local testing spots and return if matches.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return:
    """
    testing_spots = [
        {"cafeteria": (42.058813, -87.675602)},
        {"park": (42.052460, -87.669876)},
        # {"hackerspace": (42.056929, -87.676694)},
        # {"end_of_f_wing": (42.057472, -87.67662)},
        # {"atrium": (42.057323, -87.676164)},
        # {"k_wing": (42.05745, -87.675085)},
        # {"l_wing":(42.057809, -87.67611)},
        {"grocery": (42.047691, -87.679189)},
        {"grocery": (42.047691, -87.679189)},
        {"grocery": (42.047874, -87.679489)},
        {"gyms": (42.061293, -87.676620)},
        {"train_stations": (42.058623, -87.683433)},
        {"train_stations": (42.019285, -87.673238)},
        {"libraries": (42.058141, -87.674490)},
        {"field": (42.058364, -87.67089)},  # lakeside field
        {"field": (42.053160, -87.677064)},  # deering meadow, street side
        {"field": (42.053311, -87.675788)},  # deering meadow, university side
        {"parks": (42.053192, -87.676967)},  # deering meadow
        {"religious_schools": (42.056168, -87.675802)},
        {"religious_schools": (42.050438, -87.677565)},  # alice millar
        {"gyms": (42.054259, -87.678203)},  # blom
        {"gyms": (42.059575, -87.672667)},  # spac
        {"gyms": (42.059612, -87.673462)},  # spac
        {"religious_schools": (42.053232, -87.677212)},
        {"libraries": (42.053046, -87.674814)},
        {"libraries": (42.053046, -87.674814)},
        {"lakes": (47.671756, -122.344640)},  # greenlake
        {"lakes": (47.681494, -122.341121)},  # greenlake
        {"lakes": (47.680194, -122.327946)},  # greenlake
        {"parks": (47.680194, -122.327946)},  # greenlake
        {"lakes": (42.052460, -87.669876)},  # lakefill
        {"bars": (47.600759, -122.331817)},  # mccoy's
        {"parks": (47.724032, -122.337868)},  # ingraham
        # {"library": (42.053046, -87.674814)},
        # {"library": (42.053046, -87.674814)},
        # {"library": (42.053046, -87.674814)},

    ]

    close_locations = []
    for loc in testing_spots:
        dist = vincenty(loc.values()[0], (lat, lng)).meters
        if dist < 60:
            print(loc.keys()[0])
            print(dist)
            close_locations.append(loc.keys()[0])
    return close_locations


@app.route('/yelp/<string:lat>/<string:lng>', methods=['GET'])
def yelp_api(lat, lng, category_type):
    """
    Returns list of strings indicating the name of businesses and categories around the lat, lng

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :param category_type: "alias" or "name", determines if 'Vietnamese' vs 'vietnamese' will be returned
    :return: list of yelp response
    """
    print("inside yelp!")

    # run additional searches
    search_dicts = [{"lat": lat, "lng": lng, "radius": 40, "category_type": category_type, "term": ""},  # initial query
                    {"lat": lat, "lng": lng, "radius": 40, "category_type": category_type, "term": "grocery"},
                    {"lat": lat, "lng": lng, "radius": 50, "category_type": category_type, "term": "train"},
                    {"lat": lat, "lng": lng, "radius": 50, "category_type": category_type, "term": "cta"},
                    {"lat": lat, "lng": lng, "radius": 40, "category_type": category_type, "term": "bars"},
                    {"lat": lat, "lng": lng, "radius": 40, "category_type": category_type, "term": "library"},
                    {"lat": lat, "lng": lng, "radius": 40, "category_type": category_type, "term": "climbing"},
                    {"lat": lat, "lng": lng, "radius": 50, "category_type": category_type, "term": "cafeteria"},
                    {"lat": lat, "lng": lng, "radius": 50, "category_type": category_type, "term": "religious"},
                    {"lat": lat, "lng": lng, "radius": 50, "category_type": category_type, "term": "sports club"}]

    info = []
    if RUN_PARALLEL:
        pool = ThreadPool(cpu_count())
        results = pool.map(yelp_search_with_dict, search_dicts)
        pool.close()
        pool.join()

        for result in results:
            info = info + result
    else:
        for search_dict in search_dicts:
            info = info + yelp_search_with_dict(search_dict)

    print(jsonify(info))
    return info


@app.route('/test_locations/<string:lat>/<string:lng>', methods=['GET'])
def test_yelp(lat, lng):
    """
    Returns dict of strings indicating the name of businesses and categories around the lat, lng

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: dict of yelp response
    """
    print("inside yelp!")
    tags = []
    affordances = []
    names = []

    params = {
        "limit": 10,
        "sort": 1,  # sort by distance
    }
    resp = yelp_client.search_by_coordinates(float(lat), float(lng), **params)
    print(resp)
    info = []
    if not resp.businesses:
        return []
    for b in resp.businesses:
        name = b.name
        print(name)
        categories = [c[1] for c in b.categories]
        print(categories)
        info = info + [[name] + categories]
        print(info)
    return jsonify(info)


@app.route("/")
def hello():
    return "Hello World!"


# helper functions
def get_current_conditions(lat, lng):
    """
    Gets the user's current affordance state, given a latitude/longitude, and returns as an list.

    :param lat: latitude, as a float
    :param lng: longitude, as a float
    :return: list of weather, yelp API response, and local locations
    """
    current_conditions = []
    current_conditions += get_weather(lat, lng)
    current_conditions += yelp_api(lat, lng, category_type='alias')
    current_conditions += local_testing_spots(lat, lng)
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
    curr_conditions.update(local_places_keyvalues(lat, lng))
    curr_conditions.update(yelp_api_keyvalues(lat, lng))
    curr_conditions = {transform_name_to_variable(k): v for (k, v) in curr_conditions.iteritems()}
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

    for key, value in objects.iteritems():
        if key in conditions:
            conditions += value
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

    if sunset_in_utc > current_in_utc and sunrise_in_utc < current_in_utc:
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


def yelp_search(lat, lng, term, radius, category_type):
    """
    Queries Yelp API for places near the latitude/longitude specified and given a term.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :param term: location search term, as string
    :param radius: radius to search within, as float
    :param category_type: 'name' or 'alias', as string
    :return: list of Yelp locations matching term within radius of location
    """
    # setup query params
    params = {
        "radius_filter": radius,
        "limit": 3,
        "sort_by": 1  # sort by distance
    }

    if term != "":
        params["term"] = term

    # make query to yelp
    resp = yelp_client.search_by_coordinates(lat, lng, **params)

    # check if no businesses were found
    if not resp.businesses:
        return []

    # parse response if businesses were found
    info = []
    type_idx = {'name': 0, 'alias': 1}
    for b in resp.businesses:
        name = b.name
        distance = b.distance
        if distance < radius:
            print("adding: {} at distance: {} from user".format(name, distance))
            categories = [c[type_idx[category_type]] for c in b.categories]
            info = info + categories + [name]
    return info


def yelp_search_with_dict(search_dict):
    """
    Wrapper for `yelp_search` that allows for dict input. Primarily used to enable parallel execution.

    :param search_dict: dict of lat, lng, term, radius, category_type to feed into yelp_search
    :return: output from `yelp_search`
    """
    return yelp_search(search_dict["lat"], search_dict["lng"], search_dict["term"], search_dict["radius"],
                       search_dict["category_type"])


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


def test_transform_name_to_variable():
    """
    Testing for `transform_name_to_variable`.

    :return: None
    """
    assert transform_name_to_variable('Vietnamese') == 'vietnamese'
    assert transform_name_to_variable('ATV Rentals/Tours') == 'atv_rentals_tours'
    assert transform_name_to_variable('Hunting & Fishing Supplies') == 'hunting___fishing_supplies'
    assert transform_name_to_variable("May's Vietnamese Restaurant") == 'may_s_vietnamese_restaurant'


def yelp_api_keyvalues(lat, lng, category_type='name'):
    """
    Queries Yelp API and returns output as dict.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :param category_type: 'name' or 'alias', as string
    :return: dict of Yelp locations matching term within radius of location
    """
    return {key: True for key in yelp_api(lat, lng, category_type)}


def local_places_keyvalues(lat, lng):
    """
    Returns local locations, given latitude and longitude, as dict.

    :param lat: latitude, as float
    :param lng: longitude, as float
    :return: dict of local locations
    """
    return {key: True for key in local_testing_spots(lat, lng)}


if __name__ == '__main__':
    app.run(debug=True, port=int(environ.get("PORT", 5000)), host='0.0.0.0')
