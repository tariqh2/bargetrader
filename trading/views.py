import json
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from .models import Player, Trader, User, AIPlayer, Trade
from django.contrib.auth import login, authenticate
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.urls import reverse
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.db import IntegrityError
from .forms import BidOfferForm

def index(request):
    # Authenticated users view the game
    if request.user.is_authenticated:
        return render(request, "game.html")

    # Everyone else is prompted to register
    else:
        return HttpResponseRedirect(reverse("register"))
    
def register(request):
    if request.method == "POST":
        # Retrieve username from Post method
        username = request.POST["username"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user and a player based off the user
        try:
            user = User.objects.create(username=username)
            user.set_password(password)
            user.save()
            player, player_created = Player.objects.get_or_create(user=user)
            print(f'Player created: {player_created}')
            print(f'Player: {player}') 
        except IntegrityError as e:
            print(e)
            return render(request, "register.html", {
                "message": "Email address already taken."
            })
        # Authenticate the user before the login function is run
        user = authenticate(request, username=username, password=password)
        login(request, user)
        return HttpResponseRedirect(reverse("game"))
    else:
        return render(request, "register.html")

def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("game"))
        else:
            return render(request, "login.html", {
                "message": "Invalid email and/or password."
            })
    else:
        return render(request, "login.html")

@login_required
def game(request):
    username = request.user.username
    position = request.user.player.position
    pnl = request.user.player.cash_flow
    form = BidOfferForm()
    # Get all AI Players
    ai_players = AIPlayer.objects.all()
    return render(request, "game.html", {
        'username': username,
        'position': position,
        'pnl':pnl,
        'form':form,
        'ai_players':ai_players
        })

@require_POST
def update_bid_offer(request):
    form = BidOfferForm(request.POST)
    if form.is_valid():
        bid = form.cleaned_data.get("bid")
        offer = form.cleaned_data.get("offer")
        player = request.user.player
        if bid is not None:
            player.bid = bid
        if offer is not None:
            player.offer = offer
        player.save()
        return JsonResponse({"status": "success", "bid":bid, "offer":offer,"player_name":request.user.username}, status=200)
    return JsonResponse({"status": "error"}, status=400)


@require_POST
def create_trade(request):
    ai_player_id = request.POST.get("ai_player_id")
    price = request.POST.get("price")
    action = request.POST.get("action")

    # Debug: print the price value
    print(price)

    # Check if price is None
    if price is None:
        return JsonResponse({"status": "error", "message": "Price not provided."}, status=400)
    # Try to convert price to float
    try:
        price = float(price)
    except ValueError:
        return JsonResponse({"status": "error", "message": "Invalid price value."}, status=400)

    ai_player = AIPlayer.objects.get(pk=ai_player_id)
    player = request.user.player

    if action == "sell":
        buyer = ai_player
        seller = player
    else:  # action == "buy"
        buyer = player
        seller = ai_player

    trade = Trade(buyer=buyer, seller=seller, price=price)
    trade.save()

    return JsonResponse({
        "status": "success",
        "trade": {
            'id': trade.id,
            'buyer': {'name': trade.buyer.name},
            'seller': {'name': trade.seller.name},
            'price': str(trade.price),
            'quantity': trade.quantity
        }}, status=200)

    
def logout_view(request):
    logout(request)
    return redirect('index')















    