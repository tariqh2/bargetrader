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

    # Add the player to the game session via the utility method to ensure player can only be in one active game at a time
    GameSession.add_player_to_game_session(player, game_session)

    #game_session.save()

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
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        
        # Check if any of the fields are empty
        if not username or not password or not confirmation:
            return render(request, "register.html", {
                "message": "All fields are required."
            })

        # Ensure password matches confirmation
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

            # Always start a new game session for the user
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

    # Retrieve the Player instance associated with the logged-in user
    player_instance = request.user.player

    # Get the active game session for the user
    game_session = GameSession.objects.filter(players=player_instance, active=True).first()

    # If there's no active session for the user, you might want to handle this case. 
    # For instance, you could redirect them to another page or show a message.
    if not game_session:
        return render(request, "error.html", {"message": "No active game session found."})

    # Get trades for the active game session
    trades = Trade.objects.filter(game_session=game_session)

    return render(request, "game.html", {
        'username': username,
        'position': position,
        'pnl':pnl,
        'form':form,
        'ai_players':ai_players,
        'trades': trades
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

def player_summary(request):
    
    player = request.user.player
  

    # Get the latest game session for the player
    latest_game_session = player.games.order_by('-created_at').first()
 

    # If there's no game session for the player, return appropriate defaults
    if not latest_game_session:
        return JsonResponse({
            'position': 0,
            'cash_flow': 0,
            'buy_trades_count': 0,
            'sell_trades_count': 0
        })

    summary_data = {
        'position': player.calculate_position(latest_game_session),
        'cash_flow': player.calculate_cash_flow(latest_game_session),
        'buy_trades_count': player.buy_trades.filter(game_session=latest_game_session).count(),
        'sell_trades_count': player.sell_trades.filter(game_session=latest_game_session).count(),
        
    }
    return JsonResponse(summary_data)




def logout_view(request):
    # Retrieve the player instance for the logged in player
    player_instance = request.user.player

    # Get the active game session for the user 
    game_session = GameSession.objects.filter(players=player_instance, active=True).first()

    #Check if there is an active game session
    if game_session:
        # End active game session
        game_session.finish()
    
    # Logout the user
    logout(request)
    return redirect('index')















    