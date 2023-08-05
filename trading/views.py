import json
from django.contrib.auth import authenticate
from django.shortcuts import render, redirect, HttpResponse, HttpResponseRedirect
from django.contrib import messages
from .models import Player, Trader, User, AIPlayer, Trade, GameSession
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
import sys
from django.views.debug import technical_500_response

def index(request):
    # Authenticated users view the game
    if request.user.is_authenticated:
        return render(request, "game.html")

    # Everyone else is prompted to register
    else:
        return HttpResponseRedirect(reverse("register"))

def start_game_session(player):
    # Create a new game session
    game_session = GameSession.objects.create()

    # Add the AI player to the game session
    game_session.ai_players.add(*AIPlayer.objects.all())
    game_session.save()

    # Add the game session to the player
    player.games.add(game_session)
    player.save()

    # Refresh the player and game session instances
    player.refresh_from_db()
    game_session.refresh_from_db()

    # Debug print statements
    print(f'game_session.id: {game_session.id}')
    print(f'game_session.players.count: {game_session.players.count()}')
    print(f'player.games.count: {player.games.count()}')

    return game_session

    
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

        # Start a new game session for the user
        start_game_session(user.player)

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

            # Check if user has an active game session
            try:
                game_session = user.player.games.get(active=True)
            except GameSession.DoesNotExist:
                # Start a new game session for the user
                start_game_session(user.player)

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
    else:
        # Collect form error messages
        error_messages = form.non_field_errors()
        print("Form Errors:", error_messages)  # This line will print the error messages to the console.
        return JsonResponse({"status": "error", "errors": list(error_messages)}, status=400)


@require_POST
def create_trade(request):
    print(request.POST)
    try:
        ai_player_id = request.POST.get("ai_player_id")
        price = request.POST.get("price")
        action = request.POST.get("action")

        # Debug: print the price value
        print(price)

        print(f'ai_player_id={ai_player_id}, price={price}, action={action}')  # Print the incoming parameters

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

        # Get the latest game session for the player
        try:
            print(f'player.games.count={player.games.count()}')
            game_session = player.games.latest('id')
            print(f'game_session_exists={game_session is not None}')  # Print True if game_session exists, False otherwise
        except Exception as e:
            print(e) # print the exception for debugging
            return JsonResponse({"status": "error", "message": "No game session found for player."}, status=400)

        trade = Trade(buyer=buyer, seller=seller, price=price, game_session=game_session)
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
    except Exception:  # Catch all exceptions
        # If an error occurs, return the technical 500 response
        return technical_500_response(request, *sys.exc_info())



def get_game_state():
    # Get all Users and AIPlayers
    users = User.objects.all()
    ai_players = AIPlayer.objects.all()

    # Initialize lists to hold all bids and offers
    bids = []
    offers = []

    # Iterate over Users, appending their bids and offers to the appropriate lists
    for user in users:
        if hasattr(user, 'player'):  # Ensure the user has a related 'player' object
            bids.append({'player': user.player, 'bid': user.player.bid})
            offers.append({'player': user.player, 'offer': user.player.offer})

    # Iterate over AIPlayers, appending their bids and offers to the appropriate lists
    for ai_player in ai_players:
        bids.append({'player': ai_player, 'bid': ai_player.bid})
        offers.append({'player': ai_player, 'offer': ai_player.offer})

    # Return the bids and offers as a dictionary
    return {'bids': bids, 'offers': offers}






def logout_view(request):
    logout(request)
    return redirect('index')















    