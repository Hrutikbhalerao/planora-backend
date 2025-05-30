from django.contrib import admin
from django.urls import path, include
from django.http import JsonResponse

def home(request):
    return JsonResponse({"message": "Planora backend is up and running!"})

urlpatterns = [
    path('', home),  # ← add this to handle root URL
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
]
