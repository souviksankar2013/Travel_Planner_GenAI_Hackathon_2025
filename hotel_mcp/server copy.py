# server_with_fastapi.py
import asyncio
import logging
import os
import json
import re
from typing import List, Dict, Any, Optional

import requests
from fastapi import FastAPI, Body, HTTPException
import uvicorn

from fastmcp import FastMCP

logger = logging.getLogger(__name__)
logging.basicConfig(format="[%(levelname)s]: %(message)s", level=logging.INFO)

GOOGLE_MAPS_API_KEY = os.environ.get("GOOGLE_MAPS_API_KEY")

# === MCP setup ===
mcp = FastMCP("Hotel Details MCP Server")

with open("hotels_with_details.json", "r", encoding="utf-8") as f:
    Hotels: List[Dict[str, Any]] = json.load(f)


@mcp.tool()
def filter_hotels(
    room_query: Optional[str] = None,
    price_range: Optional[str] = None,  # format "min-max"
    min_rating: Optional[float] = None,
    required_facilities: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    logger.info(f">>> 🛠️ Tool: 'filter_hotels' called with room='{room_query}', price_range='{price_range}', min_rating='{min_rating}', facilities='{required_facilities}'")
    results: List[Dict[str, Any]] = []

    # Parse price range
    min_price, max_price = None, None
    if price_range:
        try:
            min_price, max_price = map(float, price_range.split("-"))
        except ValueError:
            logger.warning(f"Invalid price_range format: '{price_range}'")

    for hotel in Hotels:
        # Filter by rating
        if min_rating and hotel.get("rating", 0) < min_rating:
            continue

        # Pre-split fields
        rooms = hotel.get("room", "").split("|")
        prices = hotel.get("price", "").split("|")
        hotel_facilities = [f.strip() for f in hotel.get("facilities", "").split(",")]

        matching_rooms: List[str] = []
        matching_prices: List[float] = []

        for room, price_str in zip(rooms, prices):
            # simpler substring match (more robust for "Male Dormitory-6 hrs")
            if room_query:
                room_match = room_query.lower().strip() in room.lower()
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

        facilities_match = True
        if required_facilities:
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

    return results


def geocode_place(place_name: str):
    """Get latitude/longitude from place name using Google Maps Geocoding API"""
    if not GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set — cannot geocode.")
    url = f"https://maps.googleapis.com/maps/api/geocode/json?address={place_name}&key={GOOGLE_MAPS_API_KEY}"
    r = requests.get(url, timeout=10)
    data = r.json()
    if data.get("status") != "OK":
        raise ValueError(f"Could not geocode {place_name}: {data.get('status')}")
    loc = data["results"][0]["geometry"]["location"]
    return (loc["lat"], loc["lng"])


def get_distance(origin, destination):
    """Call Google Maps Distance Matrix API"""
    if not GOOGLE_MAPS_API_KEY:
        raise RuntimeError("GOOGLE_MAPS_API_KEY not set — cannot get distance.")
    url = (
        f"https://maps.googleapis.com/maps/api/distancematrix/json"
        f"?origins={origin[0]},{origin[1]}"
        f"&destinations={destination[0]},{destination[1]}"
        f"&key={GOOGLE_MAPS_API_KEY}"
    )
    r = requests.get(url, timeout=10)
    data = r.json()
    element = data["rows"][0]["elements"][0]
    return {
        "distance_text": element["distance"]["text"],
        "distance_value": element["distance"]["value"],  # in meters
        "duration_text": element["duration"]["text"]
    }


@mcp.tool()
def hotel_distances(hotels: List[Dict[str, Any]], tourist_places: List[str], min_rating: float = 3.0) -> str:
    filtered = [h for h in hotels if float(h.get("rating", 0)) >= min_rating]
    if not filtered:
        return "⚠️ No hotels match the criteria."

    # Geocode places
    place_coords = {p: geocode_place(p) for p in tourist_places}

    results = []
    best_hotel = None
    best_total_distance = float("inf")

    # Compute distances
    for hotel in filtered:
        origin = (hotel["latitude"], hotel["longitude"])
        hotel_result = {"name": hotel["name"], "distances": {}}
        total_distance = 0

        for place, coords in place_coords.items():
            d = get_distance(origin, coords)
            hotel_result["distances"][place] = d["distance_text"]
            total_distance += d["distance_value"]

        if total_distance < best_total_distance:
            best_total_distance = total_distance
            best_hotel = hotel_result

        results.append(hotel_result)

    # Build Markdown table
    header = "| Hotel | " + " | ".join(tourist_places) + " |"
    separator = "|" + "---|" * (len(tourist_places) + 1)
    rows = []
    for r in results:
        row = f"| {r['name']} | " + " | ".join(r["distances"][p] for p in tourist_places) + " |"
        rows.append(row)

    table = "\n".join([header, separator] + rows)
    table += f"\n\n🏆 **Best Hotel:** {best_hotel['name']}"
    return table


# === FastAPI setup ===
app = FastAPI(title="Hotel MCP API")


@app.post("/")
def root():
    return {"status": "ok", "message": "Hotel MCP API is running"}


@app.post("/filter_hotels")
def filter_hotels_http(
    room_query: Optional[str] = None,
    price_range: Optional[str] = None,
    min_rating: Optional[float] = None,
    required_facilities: Optional[str] = None,  # comma separated
):
    facilities = [f.strip() for f in required_facilities.split(",")] if required_facilities else None
    return {"output": filter_hotels(room_query, price_range, min_rating, facilities)}


@app.post("/hotel_distances")
def hotel_distances_http(payload: Dict[str, Any] = Body(...)):
    """
    POST body options:
    1) Provide `hotels` (list of hotel dicts) and `tourist_places`:
       { "hotels": [...], "tourist_places": ["Place A", "Place B"], "min_rating": 3.0 }

    2) Or provide filter params + tourist_places (server will call filter_hotels internally):
       { "room_query":"Male Dormitory", "price_range":"1000-2000", "min_rating":3.0,
         "required_facilities":["Free Wi-Fi"], "tourist_places":["Place A"] }
    """
    tourist_places = payload.get("tourist_places")
    if not tourist_places:
        raise HTTPException(status_code=400, detail="tourist_places is required")

    hotels = payload.get("hotels")
    if hotels is None:
        # try to filter using provided params
        room_query = payload.get("room_query")
        price_range = payload.get("price_range")
        min_rating = payload.get("min_rating", 3.0)
        required_facilities = payload.get("required_facilities")
        if isinstance(required_facilities, str):
            required_facilities = [f.strip() for f in required_facilities.split(",")]
        hotels = filter_hotels(room_query, price_range, min_rating, required_facilities)

    # hotels should be a list of dicts now
    if not isinstance(hotels, list):
        raise HTTPException(status_code=400, detail="hotels must be a list of hotel objects")

    min_rating = payload.get("min_rating", 3.0)

    # call existing tool function (returns markdown)
    table = hotel_distances(hotels=hotels, tourist_places=tourist_places, min_rating=min_rating)
    return {"output": table}


# === Run both MCP + FastAPI together ===
async def main():
    # Run MCP server in background (port for MCP)
    asyncio.create_task(
        mcp.run_async(
            transport="http",
            host="0.0.0.0",
            port=int(os.getenv("MCP_PORT", 8081)),
        )
    )

    # Run FastAPI (normal HTTP API)
    config = uvicorn.Config(app, host="0.0.0.0", port=int(os.getenv("PORT", 8080)), log_level="info")
    server = uvicorn.Server(config)
    await server.serve()


if __name__ == "__main__":
    asyncio.run(main())
