from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('login/', views.login_user, name='login-user'),
    path('signup/', views.signup_user, name='signup-user'),
    path('logout/', views.logout_user, name='logout'),
    path('properties/', views.properties, name='properties'),
    path('properties/<int:prop_pk>/', views.property_detail, name='property-detail'),
    path('properties/<int:prop_pk>/<int:info_pk>/integrator/', views.run_integrator, name='run-integrator')
]