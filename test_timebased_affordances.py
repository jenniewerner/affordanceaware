from sunrise_sunset import SunriseSunset
import datetime

SUNRISE_SUNSET_API = SunriseSunset()

def test_get_sunrise_sunset_at_location():

    # successful API call
    lat = 42.057238225864296
    lng = -87.67630727969825
    resp = SUNRISE_SUNSET_API.get_sunrise_sunset_at_location(lat, lng)
    print(resp)
    assert(resp is not None)
    assert(resp["sunrise"] is not None)

    sunrise_datetime_utc = datetime.datetime.strptime(resp["sunrise"], '%Y-%m-%dT%H:%M:%S+00:00')
    sunset_datetime_utc = datetime.datetime.strptime(resp["sunset"], '%Y-%m-%dT%H:%M:%S+00:00')
    print(sunrise_datetime_utc)
    print(sunset_datetime_utc)


test_get_sunrise_sunset_at_location()