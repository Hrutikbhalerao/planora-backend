from django.urls import path
from . import views
from .views import register_user, login_user, forgot_password
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from .views import save_itinerary, get_user_itineraries
urlpatterns = [
    path('generate-itinerary/', views.generate_itinerary),
    # path('available-cities/', views.get_available_cities),
      # 🔥 New endpoint
    path('register/', register_user),
    path('login/', login_user),
    path('forgot-password/', forgot_password),
    path('save-itinerary/', save_itinerary),
    path('my-itineraries/', get_user_itineraries),    
]
