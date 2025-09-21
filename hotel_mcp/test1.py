import os
import requests

key = os.environ.get("GOOGLE_MAPS_API_KEY")
url = f"https://maps.googleapis.com/maps/api/geocode/json?address=India Gate&key={key}"
r = requests.get(url)
print(r.json())
