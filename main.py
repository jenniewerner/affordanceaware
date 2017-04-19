from flask import Flask, jsonify
import pyrebase
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



YOUR_API_KEY = 'AIzaSyDBghn4IdWKYc8YC2b2N_xYf5eaouqWvtg'

google_places = GooglePlaces(YOUR_API_KEY)

app = Flask (__name__)

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


firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()
@app.route('/conditions/<string:lat>/<string:lon>', methods=['GET'])
def get_conditions(lat, lon):
    return "please use /location_tags no"

@app.route('/location_tags/<string:lat>/<string:lon>', methods=['GET'])
def get_location_tags(lat, lon):
    lat = float(lat)
    lon = float(lon)
    conditions = get_current_conditions(lat, lon)
    return jsonify(conditions)

def get_current_conditions(lat, lon):
    current_conditions = []
    current_conditions += get_weather(lat, lon)
    current_conditions += yelp_api(lat, lon)
    current_conditions += google_api(lat, lon)
    return list(set(current_conditions))

def get_weather(curr_lat, curr_lon):
    url = "http://api.openweathermap.org/data/2.5/weather?lat=" + str(curr_lat) + "&lon=" + str(curr_lon) + "&appid=" + WEATHER_API_KEY
    response = (requests.get(url)).json()
    weather = response["weather"][0]["main"]
    sunset = datetime.datetime.fromtimestamp(response["sys"]["sunset"])
    sunrise = datetime.datetime.fromtimestamp(response["sys"]["sunrise"])

    sunset_in_utc = sunset.replace(tzinfo=utc)
    sunrise_in_utc = sunrise.replace(tzinfo=utc)
    current_in_utc = datetime.datetime.now().replace(tzinfo=utc)

    tf = TimezoneFinder()
    tz = timezone(tf.timezone_at(lng=curr_lon, lat=curr_lat))
    current_local = current_in_utc.replace(tzinfo=tz)

    if(abs(sunset_in_utc - current_in_utc) <= datetime.timedelta(minutes = 15)):
        return [weather, "SUNSET"]

    if(abs(sunrise_in_utc - current_in_utc) <= datetime.timedelta(minutes = 15)):
        return [weather, "SUNRISE"]

    if sunset_in_utc >  current_in_utc and sunrise_in_utc < current_in_utc:
        return [weather, "DAYTIME"]

    if sunset_in_utc <  current_in_utc or sunrise_in_utc > current_in_utc:
        return [weather, "NIGHTTIME"]

    return []

def google_api(lat, lon):
    query_result = google_places.nearby_search(lat_lng={"lat":lat, "lng":lon}, radius=20)
    info = []
    ignore = [] #['route', 'locality', 'political']
    for place in query_result.places:
        if True not in [p in ignore for p in place.types]:
            info += [place.name] + place.types

    return info

#@app.route('/yelp', methods=['GET'])
def yelp_api(lat, lon):
    tags = []
    affordances = []
    names = []

    params = {
    	"radius_filter" : 20,
    	"limit" : 1,
        "sort" : 1, #sort by distance
    	"open_now" : True,
    }
    resp = yelp_client.search_by_coordinates(lat, lon, **params)
    if not resp.businesses:
        return []
    b = resp.businesses[0]
    name = b.name
    categories = [c[1] for c in b.categories]
    info = categories + [name]
    print info
    return info


@app.route("/")
def hello():
    return "Hello World!"


if __name__ == '__main__':
    app.run(debug=True, port=int(environ.get("PORT", 5000)), host='0.0.0.0')
