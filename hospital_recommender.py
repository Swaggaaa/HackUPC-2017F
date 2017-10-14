from googleplaces import GooglePlaces, types, lang, GooglePlacesError

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
        place = {
            'name': place.name,
            'location': place.geo_location
        }
        places.append(place) # A dict matching the JSON response from Google.
    return places[:1]