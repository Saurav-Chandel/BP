from django.contrib import admin
from django.urls import path,include
from buisness.views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'update_buisness', BuisnessViewSet, basename='user')
router.register(r'create_buisness_images', BuisnessImagesviewSet, basename='user')


app_name = "buisness"


urlpatterns = [
    # Services
    path("buisness_hours/api/v1/list/", GetAllBuisnessHours.as_view()),
    path("buisness_hours/api/v1/create/", CreateBuisnessHours.as_view()),
    path("buisness_hours/api/v1/get/<int:pk>/", GetBuisnessHours.as_view()),
    path("buisness_hours/api/v1/update/<int:pk>/", UpdateBuisnessHours.as_view()),
    path("buisness_hours/api/v1/delete/<int:pk>/", DeleteBuisnessHours.as_view()),

    # Buisness
    # path("api/v1/list/", views.GetAllBuisness.as_view()),
    # path("api/v1/create/", views.CreateBuisness.as_view()),
    # path("api/v1/get/<int:pk>/", views.GetBuisness.as_view()),
    # path("api/v1/update/<int:pk>/", views.UpdateBuisness.as_view()),
    # path("api/v1/delete/<int:pk>/", views.DeleteBuisness.as_view()),
    
    path("create_buisness_generics/", CreateBuisnessGeneric.as_view()),
    path("",include(router.urls)),

]







