from flask import Flask, jsonify
import pyrebase
import math
import json
import uuid
import requests
import datetime
from yelp.client import Client
from yelp.oauth1_authenticator import Oauth1Authenticator
from os import environ

app = Flask(__name__)

yelp_auth = auth = Oauth1Authenticator(
    consumer_key=environ.get("YELP_KEY"),
    consumer_secret=environ.get("YELP_CSECRET"),
    token=environ.get("YELP_TOKEN"),
    token_secret=environ.get("YELP_TSECRET")
)

yelp_client = Client(yelp_auth)

WEATHER_API_KEY = environ.get("WEATHER_KEY")
firebase_config = {
    "apiKey": environ.get("FIREBASE_KEY"),
    "authDomain": environ.get("FIREBASE_NAME") + ".firebaseapp.com",
    "databaseURL": "https://" + environ.get("FIREBASE_NAME") + ".firebaseio.com",
    "storageBucket": environ.get("FIREBASE_NAME") + ".appspot.com"
}

firebase = pyrebase.initialize_app(firebase_config)
db = firebase.database()


###############################
# SECONDARY CONTEXT INFORMATION
###############################


@app.route('/get_weather/<string:curr_lat>/<string:curr_lon>', methods=['GET'])
def get_weather(curr_lat, curr_lon):
    url = "http://api.openweathermap.org/data/2.5/weather?lat=" + curr_lat + "&lon=" + curr_lon + "&appid=" + WEATHER_API_KEY
    response = (requests.get(url)).json()
    # print(response)
    return response


# radius: in meters
@app.route('/get_busin_categories/<string:curr_lat>/<string:curr_lon>/<string:radius>', methods=['GET'])
def get_busin_categories(curr_lat, curr_lon, radius):
    categories = ["coffee", "parks", "gyms", "food", "beer_and_wine", "pubs", "beaches"]
    cats = []

    for c in categories:
        params = {
            "category_filter": c,
            "radius_filter": radius,
            "limit": 10,
            "open_now": True,
        }
        resp = yelp_client.search_by_coordinates(curr_lat, curr_lon, **params)
        for b in resp.businesses:
            print(b)
            cats.append(c)

    return cats


# dicts_to_output = [
#     {
#         'name': biz.name,
#         'id': biz.id,
#         'top_category': biz.categories,
#         'rating': biz.rating,
#         'review_count': biz.review_count
#     }
#    for biz in resp.businesses
# ]


@app.route('/get_businesses_by_category/<string:curr_lat>/<string:curr_lon>/<string:radius>/<string:category>',
           methods=['GET'])
def get_businesses_by_category(curr_lat, curr_lon, radius, category):
    params = {
        "category_filter": category,
        "radius_filter": float(radius),
        "open_now": True,
    }
    resp = yelp_client.search_by_coordinates(curr_lat, curr_lon, **params)
    for biz in resp.businesses:
        print(biz.categories)

    dicts_to_output = [
        {
            'name': biz.name,
            'id': biz.id,
            'categories': biz.categories,
            'rating': biz.rating,
            'review_count': biz.review_count,
            'rating': biz.rating,
            'snippet_text': biz.snippet_text,
            'location': biz.location.address,
        }
        for biz in resp.businesses
    ]
    print(dicts_to_output)
    return jsonify(dicts_to_output)


@app.route('/affordance/<string:curr_lat>/<string:curr_lon>/<string:radius>', methods=['GET'])
def get_affordance(curr_lat, curr_lon, radius):
    affordances = {
        "primary":
            {
                "location": [curr_lat, curr_lon],
                "time": [10],
            },
        "secondary": {
            "categories": get_busin_categories(curr_lat, curr_lon, radius),
            "weather": get_weather(curr_lat, curr_lon)
        }
    }

    print(affordances)
    return jsonify(affordances)


# @app.route('/affordance/<string:curr_lat>/<string:curr_lon>/<string:radius>/<string:affordance>', methods=['GET'])
# def check_for_affordance(curr_lat, curr_lon, radius, affordance):


# 	sit = {
# 			"primary":{},
# 			"secondary":{
# 				"category":[
# 					"restaurants"
# 				]
# 			}
# 		}

# 	if "category" in sit["secondary"]:
# 		c = sit["secondary"]["category"][0]
# 		resp = get_businesses_by_category(curr_lat, curr_lon, radius, c)
# 		print(resp)

# 		if resp:
# 			print("happy")
# 		else:
# 			return "False"

# 	return "True"


@app.route("/")
def hello():
    return "Hello World!"


if __name__ == '__main__':
    app.run(debug=True, port=int(environ.get("PORT", 5000)), host='0.0.0.0')
