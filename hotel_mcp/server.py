# server_fastapi_only.py
import logging
import os
import json
from typing import List, Dict, Any, Optional

import requests
from fastapi import FastAPI, Body, HTTPException
import uvicorn
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

# Load hotel data
with open("hotels_with_details.json", "r", encoding="utf-8") as f:
    Hotels: List[Dict[str, Any]] = json.load(f)


# ----------------------
# RAW LOGIC FUNCTIONS
# ----------------------
def filter_hotels_logic(
    room_query: Optional[str] = None,
    price_range: Optional[str] = None,
    min_rating: Optional[float] = None,
    required_facilities: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    """
    Filter hotels with a FIXED limit of 50.
    """
    logger.info(
        f">>> filter_hotels_logic called with room='{room_query}', "
        f"price_range='{price_range}', min_rating='{min_rating}', "
        f"facilities='{required_facilities}'"
    )

    results: List[Dict[str, Any]] = []

    # Parse price range
    min_price, max_price = None, None
    if price_range:
        try:
            min_price, max_price = map(float, price_range.split("-"))
        except ValueError:
            logger.warning(f"Invalid price_range format: '{price_range}'")

    for hotel in Hotels:
        if min_rating and hotel.get("rating", 0) < min_rating:
            continue

        rooms = hotel.get("room", "").split("|")
        prices = hotel.get("price", "").split("|")
        hotel_facilities = [f.strip().lower() for f in hotel.get("facilities", "").split(",")]

        matching_rooms, matching_prices = [], []

        for room, price_str in zip(rooms, prices):
            # Match room category
            if room_query:
                main_category = room.split("-")[0].strip().lower()
                room_match = main_category == room_query.strip().lower()
            else:
                room_match = True

            try:
                price = float(price_str)
                price_match = (min_price <= price <= max_price) if min_price is not None else True
            except ValueError:
                price_match = False

            if room_match and price_match:
                matching_rooms.append(room.strip())
                matching_prices.append(price)

        # Check facilities
        facilities_match = True
        if required_facilities:
            required_facilities = [f.lower() for f in required_facilities]
            facilities_match = all(facility in hotel_facilities for facility in required_facilities)

        if matching_rooms and facilities_match:
            results.append({
                "name": hotel.get("name"),
                "address": hotel.get("address"),
                "latitude": hotel.get("latitude"),
                "longitude": hotel.get("longitude"),
                "rating": hotel.get("rating"),
                "rooms": matching_rooms,
                "prices": matching_prices,
                "checkin": hotel.get("checkin"),
                "checkout": hotel.get("checkout"),
                "facilities": hotel.get("facilities"),
            })

    # Apply FIXED limit of 50
    return results[:10]


def geocode_place(place_name: str):
    if not GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set — cannot geocode.")
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name}&key={GOOGLE_MAPS_API_KEY}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data.get("status") != "OK":
        raise ValueError(f"Could not geocode {place_name}: {data.get('status')}")
    loc = data["results"][0]["geometry"]["location"]
    return (loc["lat"], loc["lng"])


# def get_distance(origin, destination):
#     if not GOOGLE_MAPS_API_KEY:
#         raise RuntimeError("GOOGLE_MAPS_API_KEY not set — cannot get distance.")
    
#     url = (
#         f"https://maps.googleapis.com/maps/api/distancematrix/json"
#         f"?origins={origin[0]},{origin[1]}"
#         f"&destinations={destination[0]},{destination[1]}"
#         f"&key={GOOGLE_MAPS_API_KEY}"
#     )

#     try:
#         r = requests.get(url, timeout=10)
#         r.raise_for_status()
#         data = r.json()

#         element = data.get("rows", [{}])[0].get("elements", [{}])[0]

#         distance_text = element.get("distance", {}).get("text", "N/A")
#         distance_value = element.get("distance", {}).get("value", None)
#         duration_text = element.get("duration", {}).get("text", "N/A")

#         return {
#             "distance_text": distance_text,
#             "distance_value": distance_value,
#             "duration_text": duration_text
#         }

#     except (requests.RequestException, ValueError) as e:
#         # network errors, bad JSON, etc.
#         return {
#             "distance_text": "Error",
#             "distance_value": None,
#             "duration_text": "Error",
#             "error": str(e)
#         }
    
# import requests
# import time
def chunked(seq, size):
    """Yield successive chunks from a list or tuple."""
    for i in range(0, len(seq), size):
        yield seq[i:i + size]


def get_distances_matrix_batch(origin, destinations_dict, BATCH_SIZE=25):
    """
    Fetch distances from one origin (lat, lon) to many destinations using
    Google Distance Matrix API in safe batches.

    origin: (lat, lon)
    destinations_dict: { 'Place Name': (lat, lon), ... }
    Returns: { 'Place Name': {distance_text, distance_value, duration_text, status} }
    """
    results = {}

    # Convert dict → list of (name, (lat, lon))
    destination_items = list(destinations_dict.items())

    for dest_batch in chunked(destination_items, BATCH_SIZE):
        dest_str = "|".join(f"{lat},{lon}" for _, (lat, lon) in dest_batch)
        url = (
            f"https://maps.googleapis.com/maps/api/distancematrix/json"
            f"?origins={origin[0]},{origin[1]}"
            f"&destinations={dest_str}"
            f"&key={GOOGLE_MAPS_API_KEY}"
        )

        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            data = r.json()

            if data.get("status") != "OK":
                print(f"API Error: {data.get('status')}, message: {data.get('error_message')}")
                continue

            elements = data.get("rows", [{}])[0].get("elements", [])
            for ((place_name, _), el) in zip(dest_batch, elements):
                if el.get("status") == "OK":
                    results[place_name] = {
                        "distance_value": el["distance"]["value"],
                        "distance_text": el["distance"]["text"],
                        "duration_text": el["duration"]["text"],
                        "status": "OK"
                    }
                else:
                    results[place_name] = {
                        "distance_value": None,
                        "distance_text": "N/A",
                        "duration_text": "N/A",
                        "status": el.get("status", "UNKNOWN")
                    }

        except requests.RequestException as e:
            for place_name, _ in dest_batch:
                results[place_name] = {
                    "distance_value": None,
                    "distance_text": "Error",
                    "duration_text": "Error",
                    "status": "NETWORK_ERROR",
                    "error": str(e)
                }

    return results




# def hotel_distances_logic(
#     hotels: List[Dict[str, Any]],
#     tourist_places: List[str],
#     min_rating: float = 3.0,
#     limit: int = 10
# ) -> str:
#     """
#     Sort hotels by total distance (ascending) and return top `limit` hotels.
#     Tourist places shown in a single column with line-separated distances.
#     Latitude and Longitude are also included in the output.
#     """
#     filtered = [h for h in hotels if float(h.get("rating", 0)) >= min_rating]
#     if not filtered:
#         return "No hotels match the criteria."
    
#     place_coords = {}

#     for p in tourist_places:
#         try:
#             coords = geocode_place(p)
#             place_coords[p] = coords
#         except Exception as e:
#             print(f"Skipping '{p}' due to geocoding error: {e}")
#             continue


#     # Geocode all tourist places once
#     # place_coords = {p: geocode_place(p) for p in tourist_places}

#     results = []
#     for hotel in filtered:
#         origin = (hotel["latitude"], hotel["longitude"])
#         hotel_result = {
#             "name": hotel["name"],
#             "latitude": hotel["latitude"],
#             "longitude": hotel["longitude"],
#             "distances": [],
#             "total_distance": 0,
#         }

#         # for place, coords in place_coords.items():
#         #     d = get_distance(origin, coords)
#         #     hotel_result["distances"].append(f"{place}: {d['distance_text']}")
#         #     hotel_result["total_distance"] += d["distance_value"]

#         for place, coords in place_coords.items():
#             d = get_distance(origin, coords)
#             hotel_result["distances"].append(f"{place}: {d.get('distance_text', 'N/A')}")
#             value = d.get("distance_value")
#             if isinstance(value, (int, float)):
#                 hotel_result["total_distance"] += value
#             else:
#                 print(f"Warning: Missing distance for {hotel['name']} to {place}")


#         results.append(hotel_result)

#     # Sort by total distance
#     results.sort(key=lambda x: x["total_distance"])

#     # Apply limit
#     results = results[:limit]

#     # Build markdown table
#     header = "| Hotel | Latitude | Longitude | Tourist Places | Total Distance |"
#     separator = "|---|---|---|---|---|"

#     rows = []
#     for r in results:
#         places_info = "<br>".join(r["distances"])  # line-break inside markdown cell
#         total_km = round(r["total_distance"] / 1000, 2)  # meters → km
#         row = f"| {r['name']} | {r['latitude']} | {r['longitude']} | {places_info} | {total_km} km |"
#         rows.append(row)

#     table = "\n".join([header, separator] + rows)
#     return table

def hotel_distances_logic(
    hotels: List[Dict[str, Any]],
    tourist_places: List[str],
    min_rating: float = 3.0,
    limit: int = 10
) -> str:
    """
    Sort hotels by total distance (ascending) and return top `limit` hotels.
    Uses batched Distance Matrix requests for efficiency.
    """
    filtered = [h for h in hotels if float(h.get("rating", 0)) >= min_rating]
    if not filtered:
        return "No hotels match the criteria."
    
    # Geocode all tourist places once
    place_coords = {}
    for p in tourist_places:
        try:
            coords = geocode_place(p)
            place_coords[p] = coords
        except Exception as e:
            print(f"Skipping '{p}' due to geocoding error: {e}")

    if not place_coords:
        return "No valid tourist places found."

    results = []
    for hotel in filtered:
        origin = (hotel["latitude"], hotel["longitude"])

        # Batch all tourist places for this hotel
        batch_results = get_distances_matrix_batch(origin, place_coords)

        hotel_result = {
            "name": hotel["name"],
            "latitude": hotel["latitude"],
            "longitude": hotel["longitude"],
            "distances": [],
            "total_distance": 0,
        }

        for place, d in batch_results.items():
            distance_text = d.get("distance_text") or "N/A"
            duration_text = d.get("duration_text") or "N/A"
            value = d.get("distance_value")

            # Safely accumulate total distance
            if isinstance(value, (int, float)):
                hotel_result["total_distance"] += value
            else:
                print(f"[Warning] Missing or invalid distance for '{hotel['name']}' → '{place}' (status: {d.get('status', 'Unknown')})")

            # Append formatted info for table display
            hotel_result["distances"].append(f"{place}: {distance_text} ({duration_text})")

        # Store computed result
        results.append(hotel_result)

    # Sort hotels by total distance
    results.sort(key=lambda x: x["total_distance"])
    results = results[:limit]

    # Build Markdown table
    header = "| Hotel | Latitude | Longitude | Tourist Places | Total Distance |"
    separator = "|---|---|---|---|---|"
    rows = []
    for r in results:
        places_info = "<br>".join(r["distances"])
        total_km = round(r["total_distance"] / 1000, 2)
        row = f"| {r['name']} | {r['latitude']} | {r['longitude']} | {places_info} | {total_km} km |"
        rows.append(row)

    return "\n".join([header, separator] + rows)


# ----------------------
# FastAPI setup
# ----------------------
app = FastAPI(title="Hotel API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://trip-planner-genai-hackathon.web.app"],  # only your frontend
    allow_credentials=True,
    allow_methods=["*"],  # or ["POST", "GET", "OPTIONS"]
    allow_headers=["*"],  # or ["Content-Type", "Authorization"]
)


@app.get("/")
def root():
    return {"status": "ok", "message": "Hotel API is running"}


class FilterHotelsRequest(BaseModel):
    room_query: Optional[str] = None
    price_range: Optional[str] = None
    min_rating: Optional[float] = None
    required_facilities: Optional[List[str]] = None


@app.post("/filter_hotels")
def filter_hotels_http(payload: FilterHotelsRequest):
    facilities = payload.required_facilities
    results = filter_hotels_logic(
        room_query=payload.room_query,
        price_range=payload.price_range,
        min_rating=payload.min_rating,
        required_facilities=facilities,
    )
    return {"output": results}


class HotelDistancesRequest(BaseModel):
    tourist_places: List[str]
    hotels: Optional[List[Dict[str, Any]]] = None
    room_query: Optional[str] = None
    price_range: Optional[str] = None
    min_rating: Optional[float] = 3.0
    required_facilities: Optional[List[str]] = None
    limit: Optional[int] = 10


@app.post("/hotel_distances")
def hotel_distances_http(payload: HotelDistancesRequest):
    # tourist_places is mandatory
    if not payload.tourist_places:
        raise HTTPException(status_code=400, detail="tourist_places is required")

    hotels = payload.hotels
    if hotels is None:
        # filter hotels using provided params
        hotels = filter_hotels_logic(
            room_query=payload.room_query,
            price_range=payload.price_range,
            min_rating=payload.min_rating,
            required_facilities=payload.required_facilities,
        )

    if not isinstance(hotels, list):
        raise HTTPException(status_code=400, detail="hotels must be a list of hotel objects")

    table = hotel_distances_logic(
        hotels=hotels,
        tourist_places=payload.tourist_places,
        min_rating=payload.min_rating or 3.0,
        limit=payload.limit or 10,
    )
    return {"output": table}


class GeocodeRequest(BaseModel):
    place_name: str


@app.post("/geocode")
def geocode_http(payload: GeocodeRequest):
    """
    Geocode multiple places from a comma-separated string and return as 2D array:
    [["Place Name", lat, lon], ...]
    """
    try:
        results = []
        place_list = [p.strip() for p in payload.place_name.split(",") if p.strip()]
        for place in place_list:
            lat, lon = geocode_place(place)
            results.append([place, lat, lon])
        return {"geocoded_places": results}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


if __name__ == "__main__":
    port = int(os.getenv("PORT", 8080))
    uvicorn.run("server:app", host="0.0.0.0", port=port, log_level="info")
