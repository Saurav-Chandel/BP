from django.contrib import admin
from django.urls import path,include
from buisness import views

app_name = "buisness"

urlpatterns = [
    # Services
    path("service/api/v1/list/", views.GetAllService.as_view()),
    path("service/api/v1/create/", views.CreateService.as_view()),
    path("service/api/v1/get/<int:pk>/", views.GetService.as_view()),
    path("service/api/v1/update/<int:pk>/", views.UpdateService.as_view()),
    path("service/api/v1/delete/<int:pk>/", views.DeleteService.as_view()),


    # Buisness
    path("buisness/api/v1/list/", views.GetAllBuisness.as_view()),
    path("buisness/api/v1/create/", views.CreateBuisness.as_view()),
    path("buisness/api/v1/get/<int:pk>/", views.GetBuisness.as_view()),
    path("buisness/api/v1/update/<int:pk>/", views.UpdateBuisness.as_view()),
    path("buisness/api/v1/delete/<int:pk>/", views.DeleteBuisness.as_view()),
]






