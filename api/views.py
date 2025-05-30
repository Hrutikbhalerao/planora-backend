from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.core.mail import send_mail
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.contrib.sites.shortcuts import get_current_site
from django.urls import reverse
from rest_framework.response import Response
from .models import Place
import random
import requests
from datetime import datetime, timedelta


from datetime import datetime, timedelta
import random
import requests
from django.conf import settings
from rest_framework.decorators import api_view
from rest_framework.response import Response
def get_restaurants_from_osm(city_name):
    query = f"""
    [out:json];
    area["name"="{city_name}"]->.searchArea;
    node["amenity"="restaurant"](area.searchArea);
    out;
    """
    url = "http://overpass-api.de/api/interpreter"
    try:
        response = requests.post(url, data={"data": query}, timeout=30)
        data = response.json()

        restaurants = []
        for element in data.get('elements', []):
            name = element['tags'].get('name')
            cuisine = element['tags'].get('cuisine', 'Various cuisines')
            lat = element.get('lat')
            lon = element.get('lon')

            if name and lat and lon:
                restaurants.append({
                    'name': name,
                    'cuisine': cuisine,
                    'lat': lat,
                    'lon': lon
                })

        return restaurants
    except Exception as e:
        print("Error fetching restaurants:", e)
        return []




def format_time_slot(start_time, duration_minutes):
    end_time = start_time + timedelta(minutes=duration_minutes)
    return f"{start_time.strftime('%I:%M %p')} - {end_time.strftime('%I:%M %p')}", end_time


def get_foursquare_places_by_category(category_ids, destination, limit=15):
    headers = {
        "Accept": "application/json",
        "Authorization": settings.FOURSQUARE_API_KEY
    }
    try:
        response = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers=headers,
            params={
                "categories": ",".join(category_ids),
                "near": destination,
                "sort": "RELEVANCE",
                "limit": limit
            }
        )
        return response.json().get("results", [])
    except Exception as e:
        print(f"Error fetching places by category:", e)
        return []


def get_place_photo(fsq_id):
    headers = {
        "Accept": "application/json",
        "Authorization": settings.FOURSQUARE_API_KEY
    }
    try:
        photo_resp = requests.get(
            f"https://api.foursquare.com/v3/places/{fsq_id}/photos", headers=headers)
        photos = photo_resp.json()
        if photos:
            photo = photos[0]
            return f"{photo['prefix']}original{photo['suffix']}"
    except Exception as e:
        print(f"Error fetching photo for {fsq_id}:", e)
    return None


def extract_place_data(place, destination, estimated_cost):
    loc = place.get("location", {})
    geo = place.get("geocodes", {}).get("main", {})
    fsq_id = place.get("fsq_id")
    name = place.get("name")

    if not (geo.get("latitude") and geo.get("longitude") and name):
        return None

    address = ", ".join(filter(None, [
        loc.get("address", ""),
        loc.get("locality", ""),
        loc.get("region", ""),
        loc.get("country", "")
    ]))
    image_url = get_place_photo(fsq_id)

    return {
        "name": name,
        "description": address or f"Attraction in {destination}",
        "lat": geo["latitude"],
        "lon": geo["longitude"],
        "image_url": image_url,
        "estimated_cost": estimated_cost,
    }


@api_view(['POST'])
def generate_itinerary(request):
    destination = request.data.get("destination")
    days = int(request.data.get("days", 1))
    total_budget = int(request.data.get("budget", 5000))
    per_day_budget = total_budget // days

    itinerary = {}
    # Tourist spot categories
    tourist_category_ids = ["16000", "16025", "16022", "10027", "10031", "16032"]
    entertainment_ids = ["10035"]
    shopping_ids = ["19009"]
    restaurant_ids = ["13065"]

    tourist_places = get_foursquare_places_by_category(tourist_category_ids, destination, 30)
    entertainment_places = get_foursquare_places_by_category(entertainment_ids, destination, 10)
    shopping_places = get_foursquare_places_by_category(shopping_ids, destination, 10)

    random.shuffle(tourist_places)
    random.shuffle(entertainment_places)
    random.shuffle(shopping_places)

    for day in range(days):
        itinerary[f"Day_{day + 1}"] = []
        current_time = datetime.strptime("09:00", "%H:%M")
        end_time = datetime.strptime("19:00", "%H:%M")
        used_shopping = False
        total_cost = 0

        # Define cost ranges based on budget tier
        if per_day_budget <= 1500:
            attraction_cost = 0
            restaurant_cost = 150
        elif per_day_budget <= 3000:
            attraction_cost = 150
            restaurant_cost = 300
        else:
            attraction_cost = 250
            restaurant_cost = 600
    
        # Add tourist spots
        for _ in range(3):
            if current_time >= end_time or not tourist_places:
                break
            place = tourist_places.pop()
            data = extract_place_data(place, destination, estimated_cost=attraction_cost)
            if not data:
                continue
            visit_time, current_time = format_time_slot(current_time, random.choice([60, 90]))
            itinerary[f"Day_{day + 1}"].append({**data, "time": visit_time})
            total_cost += attraction_cost
            current_time += timedelta(minutes=random.choice([10, 20]))

            if current_time.hour >= 13:
                break

        # Add lunch
        restaurant = get_foursquare_places_by_category(restaurant_ids, destination, 5)
        if restaurant:
            rest_data = extract_place_data(random.choice(restaurant), destination, estimated_cost=restaurant_cost)
            if rest_data:
                lunch_time, current_time = format_time_slot(current_time, 60)
                itinerary[f"Day_{day + 1}"].append({**rest_data, "time": lunch_time})
                total_cost += restaurant_cost
                current_time += timedelta(minutes=10)

        # Entertainment
        if entertainment_places and current_time < end_time:
            place = entertainment_places.pop()
            data = extract_place_data(place, destination, estimated_cost=attraction_cost)
            if data:
                visit_time, current_time = format_time_slot(current_time, 60)
                itinerary[f"Day_{day + 1}"].append({**data, "time": visit_time})
                total_cost += attraction_cost
                current_time += timedelta(minutes=10)

        # Shopping (once a day max)
        if not used_shopping and shopping_places and current_time < end_time:
            place = shopping_places.pop()
            data = extract_place_data(place, destination, estimated_cost=attraction_cost)
            if data:
                visit_time, current_time = format_time_slot(current_time, 45)
                itinerary[f"Day_{day + 1}"].append({**data, "time": visit_time})
                total_cost += attraction_cost
                used_shopping = True

        # Dinner
        restaurant = get_foursquare_places_by_category(restaurant_ids, destination, 5)
        if restaurant:
            rest_data = extract_place_data(random.choice(restaurant), destination, estimated_cost=restaurant_cost)
            if rest_data:
                dinner_time, _ = format_time_slot(current_time, 60)
                itinerary[f"Day_{day + 1}"].append({**rest_data, "time": dinner_time})
                total_cost += restaurant_cost

        # Add cost summary for the day
        itinerary[f"Day_{day + 1}"].append({
            "name": "Daily Total",
            "description": f"Estimated cost for Day {day+1}",
            "time": "Summary",
            "estimated_cost": total_cost
        })

    return Response({
        "destination": destination,
        "itinerary": itinerary
    })

def get_restaurant(destination, headers):
    try:
        response = requests.get(
            "https://api.foursquare.com/v3/places/search",
            headers=headers,
            params={
                "query": "restaurant",
                "near": destination,
                "limit": 10
            }
        )
        results = response.json().get("results", [])
        if not results:
            return None

        restaurant = random.choice(results)
        name = restaurant.get("name")
        if not name:
            return None

        geo = restaurant.get("geocodes", {}).get("main", {})
        loc = restaurant.get("location", {})

        address = ", ".join(filter(None, [
            loc.get("address", ""),
            loc.get("locality", ""),
            loc.get("region", ""),
            loc.get("country", "")
        ]))

        return {
            "name": name,
            "description": address or f"Restaurant in {destination}",
            "lat": geo.get("latitude"),
            "lon": geo.get("longitude")
        }
    except Exception as e:
        print("Error fetching restaurant:", e)
        return None


# @api_view(['GET'])
# def get_available_cities(request):
#     cities = Place.objects.values_list('city', flat=True).distinct()
#     return Response(sorted(set(cities)))


# ------------------ JWT Auth Views ------------------

@api_view(['POST'])
@permission_classes([AllowAny])
def register_user(request):
    username = request.data.get('username')
    email = request.data.get('email')
    password = request.data.get('password')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')

    if User.objects.filter(username=username).exists():
        return Response({'error': 'Username already exists'}, status=400)

    user = User.objects.create_user(
        username=username,
        email=email,
        password=password,
        first_name=first_name,
        last_name=last_name
    )
    user.save()
    return Response({'message': 'User registered successfully'})


@api_view(['POST'])
@permission_classes([AllowAny])
def login_user(request):
    username = request.data.get('username')
    password = request.data.get('password')

    user = authenticate(username=username, password=password)

    if user is not None:
        refresh = RefreshToken.for_user(user)
        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'username': user.username,
            'first_name': user.first_name,
        })
    else:
        return Response({'error': 'Invalid credentials'}, status=401)


@api_view(['POST'])
@permission_classes([AllowAny])
def forgot_password(request):
    email = request.data.get('email')
    try:
        user = User.objects.get(email=email)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        token = default_token_generator.make_token(user)

        current_site = get_current_site(request)
        reset_link = f"http://{current_site.domain}/reset-password/{uid}/{token}/"

        send_mail(
            subject="Password Reset Requested",
            message=f"Hi {user.username},\n\nClick the link below to reset your password:\n{reset_link}",
            from_email="admin@aitripplanner.com",
            recipient_list=[email],
            fail_silently=False,
        )

        return Response({'message': 'Password reset email sent.'})
    except User.DoesNotExist:
        return Response({'error': 'Email not found.'}, status=404)
from .models import SavedItinerary
from rest_framework.permissions import IsAuthenticated

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_itinerary(request):
    user = request.user
    destination = request.data.get('destination')
    itinerary_data = request.data.get('itinerary')

    SavedItinerary.objects.create(
        user=user,
        destination=destination,
        itinerary_data=itinerary_data
    )
    return Response({'message': 'Itinerary saved successfully!'})

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_itineraries(request):
    user = request.user
    itineraries = SavedItinerary.objects.filter(user=user).order_by('-created_at')
    data = [
        {
            'id': item.id,
            'destination': item.destination,
            'itinerary': item.itinerary_data,
            'created_at': item.created_at,
        }
        for item in itineraries
    ]
    return Response(data)
