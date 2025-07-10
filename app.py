# STAYFINDR ANALYTICS BACKEND - GDPR Compliant Analytics System
# Flask backend with hotel search + comprehensive analytics tracking
# FIXED: Hotel name-based booking URLs + Room Type Filter + Analytics Storage

import os
import json
import time
from datetime import datetime, timedelta
from urllib.parse import quote_plus
from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import requests

app = Flask(__name__)
CORS(app)

# RapidAPI Configuration
RAPIDAPI_KEY = "e1d84ea6ffmsha47402150e4b4a7p1ad726jsn90c5c8f86999"
RAPIDAPI_HOST = "booking-com18.p.rapidapi.com"

# In-memory analytics storage (for demo - use database in production)
analytics_data = {
    'events': [],
    'booking_clicks': [],
    'daily_stats': {},
    'popular_cities': {},
    'room_type_preferences': {},
    'session_data': {}
}

# European Cities Configuration - 29 major destinations
CITIES = {
    'stockholm': {
        'name': 'Stockholm, Sweden',
        'coordinates': [59.3293, 18.0686],
        'search_query': 'Stockholm Sweden'
    },
    'paris': {
        'name': 'Paris, France', 
        'coordinates': [48.8566, 2.3522],
        'search_query': 'Paris France'
    },
    'london': {
        'name': 'London, UK',
        'coordinates': [51.5074, -0.1278],
        'search_query': 'London United Kingdom'
    },
    'amsterdam': {
        'name': 'Amsterdam, Netherlands',
        'coordinates': [52.3676, 4.9041],
        'search_query': 'Amsterdam Netherlands'
    },
    'barcelona': {
        'name': 'Barcelona, Spain',
        'coordinates': [41.3851, 2.1734],
        'search_query': 'Barcelona Spain'
    },
    'rome': {
        'name': 'Rome, Italy',
        'coordinates': [41.9028, 12.4964],
        'search_query': 'Rome Italy'
    },
    'berlin': {
        'name': 'Berlin, Germany',
        'coordinates': [52.5200, 13.4050],
        'search_query': 'Berlin Germany'
    },
    'copenhagen': {
        'name': 'Copenhagen, Denmark',
        'coordinates': [55.6761, 12.5683],
        'search_query': 'Copenhagen Denmark'
    },
    'vienna': {
        'name': 'Vienna, Austria',
        'coordinates': [48.2082, 16.3738],
        'search_query': 'Vienna Austria'
    },
    'prague': {
        'name': 'Prague, Czech Republic',
        'coordinates': [50.0755, 14.4378],
        'search_query': 'Prague Czech Republic'
    },
    'madrid': {
        'name': 'Madrid, Spain',
        'coordinates': [40.4168, -3.7038],
        'search_query': 'Madrid Spain'
    },
    'milano': {
        'name': 'Milano, Italy',
        'coordinates': [45.4642, 9.1900],
        'search_query': 'Milano Italy'
    },
    'zurich': {
        'name': 'Zürich, Switzerland',
        'coordinates': [47.3769, 8.5417],
        'search_query': 'Zürich Switzerland'
    },
    'oslo': {
        'name': 'Oslo, Norway',
        'coordinates': [59.9139, 10.7522],
        'search_query': 'Oslo Norway'
    },
    'helsinki': {
        'name': 'Helsinki, Finland',
        'coordinates': [60.1695, 24.9354],
        'search_query': 'Helsinki Finland'
    },
    'warsaw': {
        'name': 'Warsaw, Poland',
        'coordinates': [52.2297, 21.0122],
        'search_query': 'Warsaw Poland'
    },
    'budapest': {
        'name': 'Budapest, Hungary',
        'coordinates': [47.4979, 19.0402],
        'search_query': 'Budapest Hungary'
    },
    'dublin': {
        'name': 'Dublin, Ireland',
        'coordinates': [53.3498, -6.2603],
        'search_query': 'Dublin Ireland'
    },
    'lisbon': {
        'name': 'Lisbon, Portugal',
        'coordinates': [38.7223, -9.1393],
        'search_query': 'Lisbon Portugal'
    },
    'brussels': {
        'name': 'Brussels, Belgium',
        'coordinates': [50.8503, 4.3517],
        'search_query': 'Brussels Belgium'
    },
    'athens': {
        'name': 'Athens, Greece',
        'coordinates': [37.9838, 23.7275],
        'search_query': 'Athens Greece'
    },
    'munich': {
        'name': 'Munich, Germany',
        'coordinates': [48.1351, 11.5820],
        'search_query': 'Munich Germany'
    },
    'lyon': {
        'name': 'Lyon, France',
        'coordinates': [45.7640, 4.8357],
        'search_query': 'Lyon France'
    },
    'florence': {
        'name': 'Florence, Italy',
        'coordinates': [43.7696, 11.2558],
        'search_query': 'Florence Italy'
    },
    'edinburgh': {
        'name': 'Edinburgh, Scotland',
        'coordinates': [55.9533, -3.1883],
        'search_query': 'Edinburgh Scotland'
    },
    'nice': {
        'name': 'Nice, France',
        'coordinates': [43.7102, 7.2620],
        'search_query': 'Nice France'
    },
    'palma': {
        'name': 'Palma, Spain',
        'coordinates': [39.5696, 2.6502],
        'search_query': 'Palma Spain'
    },
    'santorini': {
        'name': 'Santorini, Greece',
        'coordinates': [36.3932, 25.4615],
        'search_query': 'Santorini Greece'
    },
    'ibiza': {
        'name': 'Ibiza, Spain',
        'coordinates': [38.9067, 1.4206],
        'search_query': 'Ibiza Spain'
    }
}

# Country codes for localized Booking.com URLs
COUNTRY_CODES = {
    'stockholm': 'sv', 'oslo': 'no', 'helsinki': 'fi', 'copenhagen': 'dk',
    'paris': 'fr', 'lyon': 'fr', 'nice': 'fr',
    'london': 'en-gb', 'edinburgh': 'en-gb',
    'amsterdam': 'nl', 'brussels': 'nl',
    'barcelona': 'es', 'madrid': 'es', 'palma': 'es', 'ibiza': 'es',
    'rome': 'it', 'milano': 'it', 'florence': 'it',
    'berlin': 'de', 'munich': 'de',
    'vienna': 'de', 'zurich': 'de',
    'prague': 'cs', 'warsaw': 'pl', 'budapest': 'hu',
    'dublin': 'en-gb', 'lisbon': 'pt', 'athens': 'el', 'santorini': 'el'
}

# Room type configuration for enhanced search
ROOM_TYPES = {
    'single': {
        'name': 'Single Room',
        'description': 'Perfect for solo travelers',
        'default_guests': 1,
        'keywords': ['single', 'solo', 'one person', 'individual'],
        'booking_param': 'single'
    },
    'double': {
        'name': 'Double Room',
        'description': 'Ideal for couples',
        'default_guests': 2,
        'keywords': ['double', 'couple', 'two persons', 'twin'],
        'booking_param': 'double'
    },
    'family': {
        'name': 'Family Room',
        'description': 'Spacious accommodation for families',
        'default_guests': 4,
        'keywords': ['family', 'triple', 'quad', 'connecting', 'kids'],
        'booking_param': 'family'
    },
    'junior_suite': {
        'name': 'Junior Suite',
        'description': 'Spacious room with sitting area',
        'default_guests': 2,
        'keywords': ['junior suite', 'junior', 'suite', 'sitting area', 'upgraded'],
        'booking_param': 'junior_suite'
    },
    'suite': {
        'name': 'Suite/Apartment',
        'description': 'Luxury accommodation with separate living area',
        'default_guests': 3,
        'keywords': ['suite', 'apartment', 'penthouse', 'executive', 'luxury'],
        'booking_param': 'suite'
    }
}

# Analytics Helper Functions
def store_event(event_data):
    """Store analytics event with GDPR compliance"""
    # Add server timestamp
    event_data['server_timestamp'] = datetime.utcnow().isoformat()
    
    # Store in memory (use database in production)
    analytics_data['events'].append(event_data)
    
    # Update daily stats
    today = datetime.utcnow().date().isoformat()
    if today not in analytics_data['daily_stats']:
        analytics_data['daily_stats'][today] = {
            'page_views': 0,
            'searches': 0,
            'booking_clicks': 0,
            'unique_sessions': set()
        }
    
    # Update stats based on event type
    event_type = event_data.get('event_type', '')
    session_id = event_data.get('session_id', '')
    
    if event_type == 'page_view':
        analytics_data['daily_stats'][today]['page_views'] += 1
    elif event_type == 'hotel_search':
        analytics_data['daily_stats'][today]['searches'] += 1
        # Track popular cities
        city = event_data.get('city', 'unknown')
        analytics_data['popular_cities'][city] = analytics_data['popular_cities'].get(city, 0) + 1
        # Track room type preferences
        room_type = event_data.get('room_type', 'double')
        analytics_data['room_type_preferences'][room_type] = analytics_data['room_type_preferences'].get(room_type, 0) + 1
    elif event_type == 'booking_click':
        analytics_data['daily_stats'][today]['booking_clicks'] += 1
    
    if session_id:
        analytics_data['daily_stats'][today]['unique_sessions'].add(session_id)
    
    # Keep only last 30 days of events (memory management)
    cutoff_date = datetime.utcnow() - timedelta(days=30)
    analytics_data['events'] = [
        event for event in analytics_data['events']
        if datetime.fromisoformat(event['server_timestamp']) > cutoff_date
    ]
    
    print(f"📊 Analytics: Stored {event_type} event for session {session_id}")

def get_location_id(city_query):
    """Get Booking.com location ID for a city"""
    url = "https://booking-com18.p.rapidapi.com/stays/auto-complete"
    
    querystring = {"query": city_query, "languageCode": "en"}
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            data = response.json()
            if 'data' in data and data['data']:
                return data['data'][0].get('id')
    except Exception as e:
        print(f"Error getting location ID: {e}")
    
    return None

def search_hotels_booking_api(location_id, checkin, checkout, adults, rooms):
    """Search hotels using Booking.com API"""
    url = "https://booking-com18.p.rapidapi.com/stays/search"
    
    querystring = {
        "locationId": location_id,
        "checkinDate": checkin,
        "checkoutDate": checkout,
        "adults": adults,
        "rooms": rooms,
        "currency": "EUR"
    }
    
    headers = {
        "x-rapidapi-key": RAPIDAPI_KEY,
        "x-rapidapi-host": RAPIDAPI_HOST
    }
    
    try:
        response = requests.get(url, headers=headers, params=querystring)
        if response.status_code == 200:
            return response.json()
    except Exception as e:
        print(f"Error searching hotels: {e}")
    
    return None

def create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key, room_type='double'):
    """Create hotel name-based booking URL with room type for better targeting"""
    
    # Priority 1: Use direct hotel URL from API if available
    direct_urls = [
        hotel.get('url'),
        hotel.get('link'), 
        hotel.get('booking_url'),
        hotel.get('hotelUrl'),
        hotel.get('deepLink')
    ]
    
    for url in direct_urls:
        if url and 'booking.com' in str(url):
            # Add search parameters to direct URL
            separator = '&' if '?' in url else '?'
            return f"{url}{separator}checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}&room_type={room_type}"
    
    # Priority 2: Create hotel name-based search URL (IMPROVED METHOD)
    hotel_id = hotel.get('id') or hotel.get('hotel_id') or hotel.get('propertyId')
    hotel_name = hotel.get('name', 'Hotel')
    
    if hotel_id and hotel_name:
        # Get country code for the city
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        
        # Encode hotel name properly for URL
        hotel_name_encoded = quote_plus(hotel_name)
        
        # Create hotel name-based search URL
        base_params = {
            'ss': hotel_name,  # Hotel search string
            'dest_id': hotel_id,  # Hotel destination ID
            'dest_type': 'hotel',  # Specify it's a hotel
            'checkin': checkin,
            'checkout': checkout,
            'group_adults': adults,
            'no_rooms': rooms,
            'group_children': 2 if room_type == 'family' else 0,
            'room_type': ROOM_TYPES.get(room_type, {}).get('booking_param', 'double'),
            'search_selected': 'true'
        }
        
        # Build URL parameters
        params_string = '&'.join([f"{key}={quote_plus(str(value))}" for key, value in base_params.items()])
        
        return f"https://www.booking.com/searchresults.{country_code}.html?{params_string}"
    
    # Priority 3: Fallback to hotel ID-based URL
    if hotel_id:
        country_code = COUNTRY_CODES.get(city_key, 'en-gb')
        base_country = country_code.split('-')[0]
        return f"https://www.booking.com/hotel/{base_country}/?hotel_id={hotel_id}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}&room_type={room_type}"
    
    # Priority 4: Generic search by hotel name in the city
    hotel_name = hotel.get('name', '').replace(' ', '+')
    city_name = city_info['name'].replace(' ', '+')
    country_code = COUNTRY_CODES.get(city_key, 'en-gb')
    return f"https://www.booking.com/searchresults.{country_code}.html?ss={hotel_name}+{city_name}&checkin={checkin}&checkout={checkout}&group_adults={adults}&no_rooms={rooms}&room_type={room_type}"

def analyze_room_type(hotel, room_type):
    """Analyze if hotel matches requested room type"""
    hotel_name = hotel.get('name', '').lower()
    hotel_description = hotel.get('description', '').lower()
    combined_text = f"{hotel_name} {hotel_description}"
    
    if room_type in ROOM_TYPES:
        keywords = ROOM_TYPES[room_type]['keywords']
        matches = sum(1 for keyword in keywords if keyword in combined_text)
        
        # Return room description if matches found
        if matches > 0:
            return ROOM_TYPES[room_type]['description']
    
    return None

def process_hotel_data(hotels_data, city_info, checkin, checkout, adults, rooms, city_key, room_type='double'):
    """Process and format hotel data with room type analysis"""
    processed_hotels = []
    
    # Calculate nights for pricing
    try:
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
        nights = (checkout_date - checkin_date).days
    except:
        nights = 1
    
    for i, hotel in enumerate(hotels_data):
        # Extract hotel information
        hotel_name = hotel.get('name', 'Unknown Hotel')
        
        # Get real coordinates if available, otherwise use city center with offset
        latitude = hotel.get('latitude')
        longitude = hotel.get('longitude')
        
        if latitude and longitude:
            coordinates = [float(latitude), float(longitude)]
        else:
            # Fallback: spread around city center
            base_lat, base_lng = city_info['coordinates']
            coordinates = [
                base_lat + (i * 0.01) - 0.05,
                base_lng + (i * 0.01) - 0.05
            ]
        
        # Extract pricing information
        price = 'N/A'
        if 'priceBreakdown' in hotel:
            price_info = hotel['priceBreakdown'].get('grossPrice', {})
            if 'value' in price_info:
                total_price = price_info['value']
                try:
                    if nights > 0:
                        price = int(total_price / nights)
                    else:
                        price = total_price
                except:
                    price = int(total_price / 7)  # Fallback: assume 7 nights
        elif 'price' in hotel:
            price = hotel['price']
        
        # Extract rating
        rating = hotel.get('reviewScore', hotel.get('rating', 4.0))
        if rating:
            rating = float(rating) / 2 if rating > 5 else float(rating)  # Normalize to 5-point scale
        else:
            rating = 4.0
        
        # Extract address
        address = hotel.get('address', city_info['name'])
        
        # Analyze room type match
        room_description = analyze_room_type(hotel, room_type)
        
        # Create optimized booking URL with room type
        booking_url = create_booking_url(hotel, city_info, checkin, checkout, adults, rooms, city_key, room_type)
        
        processed_hotel = {
            'id': hotel.get('id') or hotel.get('hotel_id') or f"hotel_{i}",
            'name': hotel_name,
            'address': address,
            'coordinates': coordinates,
            'price': price,
            'rating': rating,
            'booking_url': booking_url,
            'room_type': room_type,
            'room_description': room_description,
            'nights': nights
        }
        
        processed_hotels.append(processed_hotel)
    
    return processed_hotels

# API Routes
@app.route('/')
def home():
    """API Documentation Page"""
    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head>
        <title>🏨 STAYFINDR Analytics Backend</title>
        <style>
            body { font-family: Arial, sans-serif; max-width: 800px; margin: 50px auto; padding: 20px; }
            h1 { color: #2c3e50; }
            .endpoint { background: #f8f9fa; padding: 15px; margin: 10px 0; border-radius: 8px; }
            .cities { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 20px 0; }
            .city { background: #e3f2fd; padding: 8px; border-radius: 4px; text-align: center; }
            .feature { background: #e8f5e8; padding: 10px; margin: 10px 0; border-radius: 8px; }
            .analytics { background: #fff3cd; padding: 10px; margin: 10px 0; border-radius: 8px; }
        </style>
    </head>
    <body>
        <h1>🏨 STAYFINDR Analytics Backend</h1>
        <p>GDPR-compliant analytics backend for European hotel search with comprehensive tracking</p>
        
        <div class="analytics">
            <strong>📊 NEW: Analytics & GDPR Compliance</strong><br>
            Complete analytics tracking system with GDPR cookie compliance, session management, and partner analytics
        </div>
        
        <div class="feature">
            <strong>✅ Hotel Search Features</strong><br>
            Hotel name-based booking URLs, room type filtering with Junior Suite, localized country URLs
        </div>
        
        <h2>Hotel Search Endpoints:</h2>
        <div class="endpoint">
            <strong>/api/hotels</strong> - Get hotels for a city<br>
            Parameters: city, room_type, checkin, checkout, adults, rooms<br>
            <em>Now with room type filtering and hotel name-based URLs</em>
        </div>
        <div class="endpoint">
            <strong>/api/cities</strong> - List all 29 cities
        </div>
        <div class="endpoint">
            <strong>/api/room-types</strong> - List all room types with Junior Suite
        </div>
        
        <h2>Analytics Endpoints:</h2>
        <div class="endpoint">
            <strong>/api/analytics/track-event</strong> - Track user events (GDPR compliant)<br>
            <em>POST: page_view, hotel_search, booking_click, room_type_change</em>
        </div>
        <div class="endpoint">
            <strong>/api/analytics/track-click</strong> - Track booking clicks for partners<br>
            <em>POST: hotel_id, hotel_name, city, room_type, price</em>
        </div>
        <div class="endpoint">
            <strong>/api/analytics/dashboard</strong> - Get analytics summary<br>
            <em>Daily stats, popular cities, room preferences</em>
        </div>
        
        <div class="endpoint">
            <strong>/test</strong> - Test Stockholm hotels with analytics
        </div>
        
        <h2>Cities supported:</h2>
        <div class="cities">
            {% for city in cities %}
            <div class="city">{{ city }}</div>
            {% endfor %}
        </div>
        
        <h2>Room Types:</h2>
        <div class="cities">
            {% for room_type, info in room_types.items() %}
            <div class="city"><strong>{{ info.name }}</strong><br><small>{{ info.description }}</small></div>
            {% endfor %}
        </div>
    </body>
    </html>
    ''', cities=list(CITIES.keys()), room_types=ROOM_TYPES)

@app.route('/api/cities')
def get_cities():
    """Get all supported cities"""
    return jsonify({
        'cities': CITIES,
        'total': len(CITIES)
    })

@app.route('/api/room-types')
def get_room_types():
    """Get all available room types"""
    return jsonify({
        'room_types': ROOM_TYPES,
        'total': len(ROOM_TYPES)
    })

@app.route('/api/hotels')
def get_hotels():
    """Get hotels for a specific city with room type filtering and analytics"""
    city = request.args.get('city', 'stockholm')
    room_type = request.args.get('room_type', 'double')
    checkin = request.args.get('checkin', '2025-07-14')
    checkout = request.args.get('checkout', '2025-07-21')
    adults = request.args.get('adults', '2')
    rooms = request.args.get('rooms', '1')
    
    if city not in CITIES:
        return jsonify({'error': f'City {city} not supported'}), 400
    
    if room_type not in ROOM_TYPES:
        return jsonify({'error': f'Room type {room_type} not supported'}), 400
    
    city_info = CITIES[city]
    room_info = ROOM_TYPES[room_type]
    
    # Get location ID for the city
    location_id = get_location_id(city_info['search_query'])
    
    if not location_id:
        return jsonify({'error': f'Could not find location ID for {city}'}), 404
    
    # Search hotels
    hotels_data = search_hotels_booking_api(location_id, checkin, checkout, adults, rooms)
    
    if not hotels_data or 'data' not in hotels_data:
        return jsonify({'error': 'No hotels found'}), 404
    
    # Process hotel data with room type analysis - limit to top 50
    processed_hotels = process_hotel_data(
        hotels_data['data'][:50], 
        city_info, 
        checkin, 
        checkout, 
        adults, 
        rooms,
        city,  # Pass city key for country code lookup
        room_type
    )
    
    # Calculate nights for pricing info
    try:
        checkin_date = datetime.strptime(checkin, '%Y-%m-%d')
        checkout_date = datetime.strptime(checkout, '%Y-%m-%d')
        nights = (checkout_date - checkin_date).days
    except:
        nights = 1
    
    return jsonify({
        'city': city_info['name'],
        'hotels': processed_hotels,
        'total_found': len(processed_hotels),
        'search_params': {
            'checkin': checkin,
            'checkout': checkout, 
            'adults': adults,
            'rooms': rooms,
            'room_type': room_type,
            'nights': nights
        },
        'room_info': {
            'type': room_type,
            'name': room_info['name'],
            'description': room_info['description'],
            'default_guests': room_info['default_guests']
        },
        'booking_optimization': 'enabled',
        'localization': 'enabled',
        'url_type': 'hotel_name_based',
        'room_filter': 'enabled',
        'analytics_enabled': True
    })

# Analytics Endpoints
@app.route('/api/analytics/track-event', methods=['POST'])
def track_event():
    """Track user events with GDPR compliance"""
    try:
        event_data = request.get_json()
        
        # Validate required fields
        if not event_data or 'event_type' not in event_data:
            return jsonify({'error': 'Missing event_type'}), 400
        
        # Store the event
        store_event(event_data)
        
        return jsonify({
            'status': 'success',
            'message': 'Event tracked successfully',
            'event_type': event_data.get('event_type'),
            'gdpr_compliant': True
        })
        
    except Exception as e:
        print(f"Analytics tracking error: {e}")
        return jsonify({'error': 'Failed to track event'}), 500

@app.route('/api/analytics/track-click', methods=['POST'])
def track_booking_click():
    """Track booking clicks for partner analytics"""
    try:
        click_data = request.get_json()
        
        # Validate required fields
        required_fields = ['hotel_id', 'hotel_name', 'city']
        if not click_data or not all(field in click_data for field in required_fields):
            return jsonify({'error': 'Missing required fields'}), 400
        
        # Add server timestamp and store
        click_data['server_timestamp'] = datetime.utcnow().isoformat()
        click_data['event_type'] = 'booking_click'
        
        # Store in booking clicks collection
        analytics_data['booking_clicks'].append(click_data)
        
        # Also store as regular event
        store_event(click_data)
        
        return jsonify({
            'status': 'success',
            'message': 'Booking click tracked successfully',
            'hotel_name': click_data.get('hotel_name'),
            'city': click_data.get('city'),
            'partner_analytics': True
        })
        
    except Exception as e:
        print(f"Booking click tracking error: {e}")
        return jsonify({'error': 'Failed to track booking click'}), 500

@app.route('/api/analytics/dashboard')
def analytics_dashboard():
    """Get analytics dashboard data"""
    try:
        # Calculate summary statistics
        total_events = len(analytics_data['events'])
        total_booking_clicks = len(analytics_data['booking_clicks'])
        
        # Get recent daily stats (last 7 days)
        recent_stats = {}
        for date, stats in list(analytics_data['daily_stats'].items())[-7:]:
            # Convert set to count for JSON serialization
            stats_copy = stats.copy()
            stats_copy['unique_sessions'] = len(stats['unique_sessions'])
            recent_stats[date] = stats_copy
        
        # Top 5 popular cities
        top_cities = dict(sorted(
            analytics_data['popular_cities'].items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:5])
        
        # Room type preferences
        room_preferences = dict(sorted(
            analytics_data['room_type_preferences'].items(), 
            key=lambda x: x[1], 
            reverse=True
        ))
        
        # Recent events (last 20)
        recent_events = analytics_data['events'][-20:]
        
        return jsonify({
            'summary': {
                'total_events': total_events,
                'total_booking_clicks': total_booking_clicks,
                'unique_cities': len(analytics_data['popular_cities']),
                'room_types_used': len(analytics_data['room_type_preferences'])
            },
            'daily_stats': recent_stats,
            'popular_cities': top_cities,
            'room_preferences': room_preferences,
            'recent_events': recent_events,
            'gdpr_compliant': True,
            'data_retention': '30 days'
        })
        
    except Exception as e:
        print(f"Dashboard error: {e}")
        return jsonify({'error': 'Failed to generate dashboard'}), 500

@app.route('/test')
def test_stockholm():
    """Test endpoint with Stockholm hotels and analytics"""
    return get_hotels()

if __name__ == '__main__':
    print("🚀 Starting STAYFINDR Analytics Backend...")
    print("🏨 Supporting 29 European cities with room type filtering")
    print("📊 GDPR-compliant analytics system enabled")
    print("🔗 Frontend should connect to this analytics backend")
    print("📋 Test API: /test")
    print("✅ Hotel search + Analytics + Room types + Localized URLs")
    
    # Use PORT environment variable for deployment (Render, Heroku, etc.)
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=True, host='0.0.0.0', port=port)
