"""bargetrader URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.urls import path
from . import views
from django.contrib import admin


urlpatterns = [
    path("", views.index, name="index"),
    path('game/', views.game, name='game'),
    path('logout/', views.logout_view, name='logout_view'),
    path("login", views.login_view, name="login"),
    path("register", views.register, name="register"),
    path("update_bid_offer/", views.update_bid_offer, name="update_bid_offer"),
    path('create_trade/', views.create_trade, name='create_trade'),
    path('player_summary/', views.player_summary, name='player_summary'),
    path('get_next_message/', views.get_next_message, name='get_next_message'),
    path('admin/', admin.site.urls),
    

]
