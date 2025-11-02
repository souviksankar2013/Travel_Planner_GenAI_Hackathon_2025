from server import filter_hotels_logic

# hotels = [
#     {"name": "Hotel A", "latitude": 28.61, "longitude": 77.23, "rating": 4.0,
#      "rooms": ["Male Dormitory"], "prices": [500], "checkin": "14:00", "checkout": "12:00",
#      "facilities": "WiFi,Parking"},
#     {"name": "Hotel B", "latitude": 28.62, "longitude": 77.22, "rating": 3.5,
#      "rooms": ["Male Dormitory"], "prices": [450], "checkin": "14:00", "checkout": "12:00",
#      "facilities": "WiFi"}
# ]

# tourist_places = ["India Gate", "Red Fort"]

# # Call the function (it will use real geocode_place and get_distance)
# result = hotel_distances(hotels, tourist_places, min_rating=3.0)

print(filter_hotels_logic("Male Dormitory","1000-2000",5.0,["Free Wi-Fi"]))