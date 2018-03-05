from flask import Flask, jsonify
import math
import json
import uuid
import requests
import datetime
from pytz import timezone, utc
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from os import environ
from googleplaces import GooglePlaces, types, lang
from timezonefinder import TimezoneFinder
from geopy.distance import vincenty
from flask_cors import CORS

YOUR_API_KEY = 'AIzaSyDBghn4IdWKYc8YC2b2N_xYf5eaouqWvtg'

google_places = GooglePlaces(YOUR_API_KEY)

app = Flask (__name__)
cors = CORS(app, resources={r"/api": {"origins": "http://localhost:3000"}})


yelp_auth = auth = Oauth1Authenticator(
    consumer_key = environ.get("YELP_KEY"),
    consumer_secret = environ.get("YELP_CSECRET"),
    token = environ.get("YELP_TOKEN"),
    token_secret = environ.get("YELP_TSECRET")
)

yelp_client = Client(yelp_auth)

WEATHER_API_KEY = environ.get("WEATHER_KEY")
firebase_config = {
  "apiKey": environ.get("FIREBASE_KEY"),
  "authDomain": environ.get("FIREBASE_NAME") + ".firebaseapp.com",
  "databaseURL": "https://"+environ.get("FIREBASE_NAME") +".firebaseio.com",
  "storageBucket": environ.get("FIREBASE_NAME") + ".appspot.com"
}


@app.route('/conditions/<string:lat>/<string:lon>', methods=['GET'])
def get_conditions(lat, lon):
    return []


@app.route('/location_tags/<string:lat>/<string:lon>', methods=['GET'])
def get_location_tags(lat, lon):
    lat = float(lat)
    lon = float(lon)
    conditions = get_current_conditions(lat, lon)
    return jsonify(conditions)


@app.route('/location_keyvalues/<string:lat>/<string:lon>', methods=['GET'])
def get_location_keyvalues(lat, lon):
    lat = float(lat)
    lon = float(lon)
    conditions = get_current_conditions_as_keyvalues(lat, lon)
    return jsonify(conditions)


@app.route('/search/<string:cat>', methods=['GET'])
def get_search(cat):
    params = {
        "term": cat,
        "radius_filter" : 500,
        #"limit": 20,
        "sort" : 1, #sort by distance
        #"open_now" : True,
    }
    resp = yelp_client.search_by_coordinates(42.046876, -87.679532, **params)
    info = []
    if not resp.businesses:
        return []
    for b in resp.businesses:
        name = b.name
        name = name.replace(" ", "_")
        categories = [c[1] for c in b.categories]
        info = info  + [name, categories]

    return jsonify(info)


def get_current_conditions(lat, lon):
    current_conditions = []
    current_conditions += get_weather(lat, lon)
    current_conditions += yelp_api(lat, lon, category_type='alias')
    current_conditions += local_testing_spots(lat, lon)
    #current_conditions += google_api(lat, lon)
    current_conditions = map(lambda x: x.lower(), list(set(current_conditions)))

    get_objects(current_conditions)
    print current_conditions
    return current_conditions


def get_current_conditions_as_keyvalues(lat, lon):
    curr_conditions = {}
    curr_conditions.update(get_weather_time_keyvalues(lat, lon))
    curr_conditions.update(local_places_keyvalues(lat, lon))
    curr_conditions.update(yelp_api_keyvalues(lat, lon))
    curr_conditions = {transform_name_to_variable(k): v
                       for (k, v) in curr_conditions.iteritems()}
    return curr_conditions



def get_objects(conditions):
    objects = {"beaches": ["waves", "build_a_sandcastle"], "northwestern_university_library": ["castle"],
               "coffee": ["chair", "sit_in_a_chair"], "parks": ["trees", "grass", "frolick", "hug_a_tree", "pick_a_leaf"],
               "hackerspace": ["computer", "relax_in_a_chair", "surf_the_interweb"],
               "trainstations": ["train", "ride_a_train"], "northwestern_university_sailing_center": ["sailboat"],
            }

    for key, value in objects.iteritems():
        if key in conditions:
            conditions+= value
    return conditions

@app.route('/local_testing/<string:lat>/<string:lon>', methods=['GET'])
def local_testing_spots(lat, lon):
    testing_spots = [
        {"cafeteria": (42.058813,-87.675602)},
        {"park": (42.052460,-87.669876)},
        # {"hackerspace": (42.056929, -87.676694)},
        # {"end_of_f_wing": (42.057472, -87.67662)},
        # {"atrium": (42.057323, -87.676164)},
        # {"k_wing": (42.05745, -87.675085)},
        # {"l_wing":(42.057809, -87.67611)},
        {"grocery": (42.047691, -87.679189)},
        {"grocery": (42.047691, -87.679189)},
        {"grocery": (42.047874, -87.679489)},
        {"gym": (42.061293,-87.676620)},
        {"train_stations": (42.058623,-87.683433)},
        {"train_stations": (42.019285,-87.673238)},
        {"library": (42.058141,-87.674490)},
        {"field": (42.058364,-87.67089)}, #lakeside field
        {"field": (42.053160, -87.677064)}, #deering meadow, street side
        {"field": (42.053311, -87.675788)}, #deering meadow, university side
        {"park": (42.053192,-87.676967)}, #deering meadow
        {"religious_schools": (42.056168,-87.675802)},
        {"religious_schools": (42.050438,-87.677565)}, #alice millar
        {"gym": (42.054259, -87.678203)},#blom
        {"gym": (42.059575, -87.672667)},#spac
        {"gym": (42.059612, -87.673462)}, #spac
        {"religious_schools": (42.053232, -87.677212)},
        {"library": (42.053046, -87.674814)},
        {"library": ( 42.053046, -87.674814)},
        {"lake": (47.671756, -122.344640)}, #greenlake
        {"lake": (47.681494, -122.341121)}, #greenlake
        {"lake": (47.680194, -122.327946)}, #greenlake
        {"park": (47.680194, -122.327946)}, #greenlake
        {"lake": (42.052460,-87.669876)}, #lakefill
        {"bar": (47.600759, -122.331817)}, #mccoy's
        {"park": (47.724032, -122.337868)}, #ingraham 
        # {"library": (42.053046, -87.674814)},
        # {"library": (42.053046, -87.674814)},
        # {"library": (42.053046, -87.674814)},

                     ]

    close_locations = []
    for loc in testing_spots:
        dist = vincenty(loc.values()[0], (lat, lon)).meters
        if( dist < 60):
            print loc.keys()[0]
            print dist
            close_locations.append(loc.keys()[0])
    return close_locations


def make_weather_request(curr_lat, curr_lon):
    url = "http://api.openweathermap.org/data/2.5/weather?lat=" + str(curr_lat) + "&lon=" + str(curr_lon) + "&appid=" + WEATHER_API_KEY
    response = (requests.get(url)).json()
    return response

def make_forcast_request(curr_lat, curr_lon):
    url = "http://api.openweathermap.org/data/2.5/forecast?lat=" + str(curr_lat) + "&lon=" + str(curr_lon) + "&appid=" + WEATHER_API_KEY
    response = (requests.get(url)).json()
    return response

def period_of_day(current_in_utc, sunrise_in_utc, sunset_in_utc):
    """ return sunset, sunrise, daytime, or nighttime given values in utc """
    if (abs(sunset_in_utc - current_in_utc) <= datetime.timedelta(minutes=25)):
        return "sunset"

    if (abs(sunrise_in_utc - current_in_utc) <= datetime.timedelta(minutes=25)):
        return "sunrise"

    if sunset_in_utc > current_in_utc and sunrise_in_utc < current_in_utc:
        return "daytime"

    if sunset_in_utc < current_in_utc or sunrise_in_utc > current_in_utc:
        return "nighttime"


def get_local_time(curr_lat, curr_lon):
    """ given a location, find the current local time in that time zone """
    tf = TimezoneFinder()
    tz = timezone(tf.timezone_at(lng=curr_lon, lat=curr_lat))
    current_local = datetime.datetime.now(tz)
    return current_local


def get_weather(curr_lat, curr_lon):
    response = make_weather_request(curr_lat, curr_lon)
    weather = response["weather"][0]["main"]
    sunset = datetime.datetime.fromtimestamp(response["sys"]["sunset"])
    sunrise = datetime.datetime.fromtimestamp(response["sys"]["sunrise"])

    sunset_in_utc = sunset.replace(tzinfo=utc)
    sunrise_in_utc = sunrise.replace(tzinfo=utc)
    current_in_utc = datetime.datetime.now().replace(tzinfo=utc)

    return [weather, period_of_day(current_in_utc, sunrise_in_utc,
                                   sunset_in_utc)]


def get_weather_time_keyvalues(curr_lat, curr_lon):
    forcast_response = make_forcast_request(curr_lat, curr_lon)
    response = make_weather_request(curr_lat, curr_lon)

    weather_tags_list = [weather["main"] for weather in response['weather']]
    kv = {weather_key: True for weather_key in weather_tags_list}

    sunset = datetime.datetime.fromtimestamp(response["sys"]["sunset"])
    sunrise = datetime.datetime.fromtimestamp(response["sys"]["sunrise"])

    sunset_in_utc = sunset.replace(tzinfo=utc)
    sunrise_in_utc = sunrise.replace(tzinfo=utc)
    current_in_utc = datetime.datetime.now().replace(tzinfo=utc)
    kv[period_of_day(current_in_utc, sunrise_in_utc, sunset_in_utc)] = True

    for prediction in forcast_response["list"]:
        forcast_dt = datetime.datetime.fromtimestamp(prediction["dt"])
        forcast_dt = forcast_dt.replace(tzinfo=utc)

        if(abs(sunset_in_utc - forcast_dt) <= datetime.timedelta(hours=3)):
            if(sunset_in_utc.weekday() == forcast_dt.weekday()):
                kv["sunset_predicted_weather"] = "\"" + prediction["weather"][0]["main"].lower() + "\""
                break

    current_local = get_local_time(curr_lat, curr_lon)
    kv["utc_offset"] = current_local.utcoffset().total_seconds()/60/60
    kv["hour"] = current_local.hour
    kv["minute"] = current_local.minute
    #kv["sunset_time"] = sunset
    kv["sunset_time_minutes"] = sunset.minute
    kv[current_local.tzinfo.zone] = True
    days_of_the_week = ["monday", "tuesday", "wednesday", "thursday", "friday",
                        "saturday", "sunday"]
    kv[days_of_the_week[current_local.weekday()]] = True  # "wednesday": True

    return kv


def google_api(lat, lon):
    query_result = google_places.nearby_search(lat_lng={"lat":lat, "lng":lon}, radius=20)
    info = []
    ignore = [] #['route', 'locality', 'political']
    for place in query_result.places:
        if True not in [p in ignore for p in place.types]:
            info += [place.name] + place.types

    return info

def yelp_search(lat, lon, term, radius, category_type):
    info = []
    params = {
        "radius_filter" : radius,
        "limit" : 3,
        "sort_by" : "distance", #sort by distance
        "open_now" : True,
        "term": term
    }
    resp = yelp_client.search_by_coordinates(lat, lon, **params)
    if not resp.businesses:
        return []
    type_idx = {'name': 0, 'alias': 1}
    for b in resp.businesses:
        name = b.name
        # print "we see " + name + " " + str(b.distance)
        if( b.distance < radius ):
            print "adding" + name
            categories = [c[type_idx[category_type]] for c in b.categories]
            info = info + categories + [name]
    return info


@app.route('/yelp/<string:lat>/<string:lon>', methods=['GET'])
def yelp_api(lat, lon, category_type):
    """Returns list of strings indicating the name of businesses and categories around the lat, lon
    lat: float
    lon: float
    type: "alias" or "name", determines if 'Vietnamese' vs 'vietnamese' will be returned
    """
    print "inside yelp!"
    tags = []
    affordances = []
    names = []

    params = {
    	"radius_filter" : 40,
    	"limit" : 3,
        "sort_by" : "distance", #sort by distance
    	"open_now" : True,
    }
    resp = yelp_client.search_by_coordinates(lat, lon, **params)
    print "first pass"
    print resp
    info = []
    if not resp.businesses:
        print "no businesses"
    type_idx = {'name': 0, 'alias': 1}
    for b in resp.businesses:
        name = b.name
        print name
        print b.distance
        categories = [c[type_idx[category_type]] for c in b.categories]
        info = info + categories + [name]

    info = info + yelp_search(lat, lon, "grocery", 40, category_type,)
    info = info + yelp_search(lat, lon, "train", 50, category_type)
    info = info + yelp_search(lat, lon, "cta", 50, category_type)

    info = info + yelp_search(lat, lon, "bars", 40, category_type)
    info = info + yelp_search(lat, lon, "library", 40, category_type)
    info = info + yelp_search(lat, lon, "climbing", 40, category_type)
    info = info + yelp_search(lat, lon, "cafeteria", 50, category_type)
    info = info + yelp_search(lat, lon, "religious", 50, category_type)
    info = info + yelp_search(lat, lon, "sports club", 50, category_type)



    print jsonify(info)
    return info


def transform_name_to_variable(category_name):
    """ this is neccessary to get the category names to align with the variables
    that are created in affinder
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
    assert transform_name_to_variable('Vietnamese') == 'vietnamese'
    assert transform_name_to_variable('ATV Rentals/Tours') == 'atv_rentals_tours'
    assert transform_name_to_variable('Hunting & Fishing Supplies') == 'hunting___fishing_supplies'
    assert transform_name_to_variable("May's Vietnamese Restaurant") == 'may_s_vietnamese_restaurant'


def yelp_api_keyvalues(lat, lon, category_type='name'):
    return {key: True for key in yelp_api(lat, lon, category_type)}

def local_places_keyvalues(lat, lon):
    return {key: True for key in local_testing_spots(lat, lon)}

@app.route('/test_locations/<string:lat>/<string:lon>', methods=['GET'])
def test_yelp(lat, lon):
    print "inside yelp!"
    tags = []
    affordances = []
    names = []

    params = {
        "limit" : 10,
        "sort" : 1, #sort by distance
    }
    resp = yelp_client.search_by_coordinates(float(lat), float(lon), **params)
    print resp
    info = []
    if not resp.businesses:
        return []
    for b in resp.businesses:
        name = b.name
        print name
        categories = [c[1] for c in b.categories]
        print categories
        info = info + [[name]+categories]
        print info
    return jsonify(info)


@app.route("/")
def hello():
    return "Hello World!"


if __name__ == '__main__':
    app.run(debug=True, port=int(environ.get("PORT", 5000)), host='0.0.0.0')
