import os
import json
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS
from urllib.parse import quote_plus

app = Flask(__name__)
CORS(app)

# RapidAPI Keys
HOTELS_RAPIDAPI_KEY = "DIN_API_NYCKEL"
HOTELS_RAPIDAPI_HOST = "hotels4.p.rapidapi.com"

# European Cities
CITIES = {
    'stockholm': {
        'name': 'Stockholm',
        'coordinates': [59.3293, 18.0686],
        'search_query': 'Stockholm Sweden'
    },
    'paris': {
        'name': 'Paris',
        'coordinates': [48.8566, 2.3522],
        'search_query': 'Paris France'
    },
    # ... Lägg till fler städer vid behov
}

# ==================== HOTELS.COM API ====================

def get_hotels_destination_id(city_name):
    url = "https://hotels4.p.rapidapi.com/locations/v3/search"
    querystring = {"q": city_name, "locale": "en_US"}
    headers = {
        "x-rapidapi-key": HOTELS_RAPIDAPI_KEY,
        "x-rapidapi-host": HOTELS_RAPIDAPI_HOST
    }
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            for result in data.get('sr', []):
                if result.get('type') == 'CITY':
                    return result.get('gaiaId')
    except Exception as e:
        print(f"Error getting Hotels.com destination ID: {e}")
    return None

def search_hotels_hotels_api(destination_id, checkin, checkout, adults, rooms):
    url = "https://hotels4.p.rapidapi.com/properties/v2/list"
    payload = {
        "currency": "EUR",
        "eapid": 1,
        "locale": "en_US",
        "siteId": 300000001,
        "destination": {"regionId": str(destination_id)},
        "checkInDate": {
            "day": int(checkin.split('-')[2]),
            "month": int(checkin.split('-')[1]),
            "year": int(checkin.split('-')[0])
        },
        "checkOutDate": {
            "day": int(checkout.split('-')[2]),
            "month": int(checkout.split('-')[1]),
            "year": int(checkout.split('-')[0])
        },
        "rooms": [{"adults": int(adults), "children": []}],
        "resultsStartingIndex": 0,
        "resultsSize": 25,
        "sort": "PRICE_LOW_TO_HIGH"
    }
    headers = {
        "content-type": "application/json",
        "x-rapidapi-key": HOTELS_RAPIDAPI_KEY,
        "x-rapidapi-host": HOTELS_RAPIDAPI_HOST
    }
    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error searching Hotels.com hotels: {e}")
    return None

def fetch_hotels_com_data(city_info, checkin, checkout, adults, rooms):
    city_name = city_info.get('name')
    if not city_name:
        print("❌ city_info saknar 'name'")
        return None
    destination_id = get_hotels_destination_id(city_name)
    if not destination_id:
        print(f"❌ Kunde inte hitta destination ID för: {city_name}")
        return None
    hotels_response = search_hotels_hotels_api(destination_id, checkin, checkout, adults, rooms)
    if not hotels_response:
        print("❌ Hotels.com API svarar inte med data")
        return None
    if isinstance(hotels_response, dict) and (
        'propertySearch' in hotels_response or 'properties' in hotels_response
    ):
        return {'data': hotels_response}
    print("❌ Hotels.com data saknar förväntad struktur")
    return None

# ==================== HOTELLBEARBETNING ====================

def process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms):
    processed_hotels = []
    if not isinstance(hotels_data, dict) or 'data' not in hotels_data:
        return processed_hotels

    data = hotels_data.get('data')
    properties = []
    if isinstance(data, dict):
        properties = (
            data.get('propertySearch', {}).get('properties') or
            data.get('properties') or []
        )
    elif isinstance(data, list):
        properties = data

    for i, hotel in enumerate(properties[:25]):
        if not isinstance(hotel, dict):
            continue

        hotel_name = hotel.get('name') or f"Hotel {i+1}"
        coordinates = city_info.get('coordinates', [0.0, 0.0])
        lat = (
            hotel.get('mapMarker', {}).get('latLong', {}).get('lat') or
            hotel.get('mapMarker', {}).get('latLong', {}).get('latitude') or
            hotel.get('coordinate', {}).get('lat') or
            hotel.get('coordinate', {}).get('latitude')
        )
        lon = (
            hotel.get('mapMarker', {}).get('latLong', {}).get('lon') or
            hotel.get('mapMarker', {}).get('latLong', {}).get('longitude') or
            hotel.get('coordinate', {}).get('lon') or
            hotel.get('coordinate', {}).get('longitude')
        )
        try:
            coordinates = [float(lat), float(lon)]
        except (TypeError, ValueError):
            pass

        price = hotel.get('price', {}).get('lead', {}).get('amount')
        try:
            price = int(price)
        except (TypeError, ValueError):
            price = 'N/A'

        rating = hotel.get('reviews', {}).get('score') or hotel.get('guestReviews', {}).get('rating')
        try:
            rating = float(rating)
        except (TypeError, ValueError):
            rating = 4.0

        property_id = hotel.get('id') or hotel.get('propertyId') or str(i)
        hotels_url = (
            f"https://hotels.com/h{property_id}.Hotel-Information?"
            f"checkIn={checkin}&checkOut={checkout}&rooms[0].adults={adults}&rooms[0].children=0"
        )

        address = city_info.get('name')
        neighborhood = hotel.get('neighborhood')
        if isinstance(neighborhood, dict):
            address = neighborhood.get('name') or address
        else:
            street = hotel.get('address', {}).get('streetAddress')
            if street:
                address = street

        processed_hotels.append({
            'id': f"hotels_{property_id}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'platform': 'Hotels.com',
            'platform_logo': '🏛️',
            'booking_url': hotels_url,
            'source': 'hotels'
        })

    return processed_hotels

# ==================== HUVUDFUNKTION ====================

@app.route("/test")
def get_hotels_multiplatform():
    try:
        city_key = request.args.get('city', 'stockholm').lower()
        city_info = CITIES.get(city_key)
        if not city_info:
            return jsonify({'error': 'Ogiltig stad'}), 400

        checkin = request.args.get('checkin', '2025-08-01')
        checkout = request.args.get('checkout', '2025-08-03')
        adults = int(request.args.get('adults', 1))
        rooms = int(request.args.get('rooms', 1))

        hotels_data = fetch_hotels_com_data(city_info, checkin, checkout, adults, rooms)
        hotels_com_hotels = process_hotels_com_hotels(hotels_data, city_info, checkin, checkout, adults, rooms)
        sorted_hotels = sorted(hotels_com_hotels, key=lambda h: h.get('rating', 0), reverse=True)

        return jsonify(sorted_hotels)

    except Exception as e:
        print(f"🔥 get_hotels_multiplatform error: {e}")
        return jsonify({'error': 'Kunde inte hämta hotellinformationen.'}), 500
