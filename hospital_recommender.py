from googleplaces    import GooglePlaces, types, lang, GooglePlacesError
from geopy.geocoders import Nominatim
YOUR_API_KEY = 'AIzaSyBDmWXiD0xaLmI9TCWowBShPRjzfynXMPY'


def near_specialist(lat,lng, key_words=None):
    google_places = GooglePlaces(YOUR_API_KEY)
    query_result = google_places.nearby_search(
                        lat_lng={
                            'lat':lat,
                            'lng':lng
                        },
                        radius=2000,
                        types=[types.TYPE_HOSPITAL]
                    )

    places = []
    for place in query_result.places:
        place2 = {
            'name': place.name,
            'location': place.geo_location
        }
        if len(places)==3: break
        else: places.append(place2) # A dict matching the JSON response from Google.
    return places

def city_exists(city):
    geolocator = Nominatim()
    return geolocator.geocode(city)!=None

def get_city_name(lat, lgt):
    geolocator = Nominatim()
    try:
        location = geolocator.reverse("{}, {}".format(str(lat),
                                                    str(lgt)
                                                    ))
    except:
        return None
    return location.raw['address']['town']

def get_city_location(city):
    geolocator = Nominatim()
    return geolocator.geocode(city)