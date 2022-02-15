from django.contrib import admin
from django.urls import path,include
from adminapp.views import Login
from django.contrib.auth import login
from adminapp.views import *
from adminapp import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    # path('',auth_views.LoginView.as_view(), name='login'),
    # path('',Login.as_view(),name='login'),  
    path('login/',Login,name='login'),
    path('logout/',logout,name='logout'),
    path('suspend/',suspend,name='suspend'),
    path('dashboard/',dashboard,name='dashboard'),
    path('BusinessManagement/',buisness_management,name='buisness_management'),
    path('report/',report_management,name='report_management'),
    path('UserManagement/',user_management,name='user_management'),
    # path('change_password/',views.Change_Password.as_view(),name='change_password'),
    path('forgot_password/',views.forgot_password.as_view(),name='forgot_password'),
    path(
        'auth-change-password/',
        auth_views.PasswordChangeView.as_view(
            template_name='commons/change_password.html',
            success_url = '/'
        ),
        name='change_password'
    ),

    path('password_reset/', auth_views.PasswordResetView.as_view(), name='password_reset'),
    path('password_reset/done/', auth_views.PasswordResetDoneView.as_view(), name='password_reset_done'),
    path('reset/<uidb64>/<token>/',
        auth_views.PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('reset/done/', auth_views.PasswordResetCompleteView.as_view(), name='password_reset_complete'),
]



    