# Affordance Aware API

## Development
We use [pipenv](https://github.com/pypa/pipenv) for managing package dependencies.

1. Install pipenv using the link above.
2. Run `pipenv install` to install package dependencies and `pipenv shell` to start virtual environment with installed dependencies.
3. Run `python main.py` to start server and make requests to [http://0.0.0.0:5000/](http://0.0.0.0:5000/).

## Usage
When deployed, make a GET request to the following URL:
```
https://affordanceaware.herokuapp.com/location_tags/<latitude>/<longitude>
```

The request will return a JSON with the following fields:
* affordances -- array of affordance
* daylight -- either true, false or SUNSET
* hours -- hour of current time
* location_names -- array of names of nearby locations
* location_tags -- array of objects at nearby locations
* minutes -- minutes of current time
* weather -- descption of current weather, see range of options [here](https://openweathermap.org/weather-conditions)

Supported location types include:
* Northwestern classrooms
* Northwestern student housing
* coffee shops
* parks
* gyms
* restaurants

Example query while at a coffee shop in the evening:
```
GET https://affordanceaware.herokuapp.com/location_tags/42.0582565/-87.6841178
{
  "affordances": [
    "eat",
    "people_watch",
    "sit"
  ],
  "daylight": false,
  "hours": 17,
  "location_names": [
    "coffee"
  ],
  "location_tags": [
    "food",
    "people",
    "table"
  ],
  "minutes": 6,
  "weather": "clear sky "
}
```
