from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone
from django.db.models import Q
import random
from django.db import transaction
from decimal import Decimal



# Create your models here.

''' 
    Set up a base class called Trader for Player and AIPlayer to inherit. 
'''

class Trader(models.Model):
    name = models.CharField(max_length=200)

    # This method calculates the position by summing all the buy and sell trades

    def calculate_position(self, game_session=None):
        buy_trade_queryset = self.buy_trades.all()
        sell_trade_queryset = self.sell_trades.all()

        # If a game_session is provided, filter the trades by that session
        if game_session:
            buy_trade_queryset = buy_trade_queryset.filter(game_session=game_session)
            sell_trade_queryset = sell_trade_queryset.filter(game_session=game_session)

        # Use filtered query for aggregation
        buy_trades = buy_trade_queryset.aggregate(Sum('quantity'))['quantity__sum']  
        sell_trades = sell_trade_queryset.aggregate(Sum('quantity'))['quantity__sum']  

        # If there are no buy or sell trades, set position to 0
        buy_trades_total = buy_trades if buy_trades else 0
        sell_trades_total = sell_trades if sell_trades else 0

        position = buy_trades_total - sell_trades_total
        return position
    
    # This method calculates the total cash flow for buy and sell trades made by the trader

    def calculate_cash_flow(self, game_session=None):
        cash_flow = 0

        buy_trade_queryset = self.buy_trades.all()
        sell_trade_queryset = self.sell_trades.all()

        # If a game_session is provided, filter the trades by that session
        if game_session:
            buy_trade_queryset = buy_trade_queryset.filter(game_session=game_session)
            sell_trade_queryset = sell_trade_queryset.filter(game_session=game_session)

        for trade in buy_trade_queryset:
            cash_flow -= trade.quantity * trade.price
        
        for trade in sell_trade_queryset:
            cash_flow += trade.quantity * trade.price
        
        return cash_flow


    def update_position(self):
        position = self.calculate_position()
        self.position = position
        self.save()
    
    def update_cash_flow(self):
        cash_flow = self.calculate_cash_flow()
        self.cash_flow = cash_flow
        self.save()   

    def __str__(self):
        return self.name

class Player(Trader):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    position = models.IntegerField(default=0)  # Add the 'position' field with a default value of 0
    cash_flow = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    bid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    offer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    games = models.ManyToManyField('trading.GameSession', related_name='games')

    def save(self, *args, **kwargs):
        self.name = self.user.username
        super().save(*args, **kwargs)
    
    def calculate_total_pnl(self):
        return self.cash_flow    

    def __str__(self):
        return self.user.username

class AIPlayer(Trader):
    style = models.CharField(max_length=200)
    bid = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    offer = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    current_ev = models.DecimalField(max_digits=10, decimal_places=4, default=Decimal('0.00'))


    def __str__(self):
        return f"AI Player: {self.name}, Style: {self.style}"
    

    # Constants for impact and uncertainty values
    adjustment_factor = Decimal("0.05")  # 5% impact on expected value
    UNCERTAINTY_FACTOR = Decimal("0.10")  # 10% uncertainty factor

    def compute_ev(self, initial_price, message):
        """
        Compute the Expected Value based on the message impact.
        If no current EV has been set, it initializes with the game's initial price.
        """
        if self.current_ev == Decimal('0.00'):
            self.current_ev = initial_price

        if message.impact_type == "bullish":
            self.current_ev *= (1 + AIPlayer.adjustment_factor)
        elif message.impact_type == "bearish":
            self.current_ev *= (1 - AIPlayer.adjustment_factor)
        
        # Save the updated Expected Value
        self.save()

        return self.current_ev
    
    def decide_to_trade(self,player):
        """
        This function determines whether or not the AI Player will trade with the player based on
        assessing the  computed expected value of the game with the active bids and offers of the Player.
        
        """

        # 1. Retrieve the active game session for the player.
        active_game_session = player.games.filter(active=True).first()
        if not active_game_session:
            return 'none'  # No active game session found for the player, so no decision made.
        
        # 2. Fetch the bid and offer for the player.
        player_bid = player.bid
        player_offer = player.offer

        # 3. Retrieve the current_ev 
        ai_current_ev = self.current_ev

        
        #4. Check if the player bid and offer is not zero.
        if player_bid != Decimal('0.00') or player_offer != Decimal('0.00'):

            if ai_current_ev > player_offer: 
                # Current expected value is higher than player's offer -> AI buys from player at player's offer price
                return self.initiate_trade(player, "buy", player_offer, active_game_session)
            
            if ai_current_ev < player_bid: 
                # Current expected value is lower than player's bid -> AI sells to player at player's bid price
                return self.initiate_trade(player, "sell", player_bid, active_game_session)

        # No opportunity to trade.
        return 'no_opportunity_to_trade'

    def initiate_trade(self, player, action, price, game_session):
        """
        This function creates a trade between the AI and the player.
        """
        if action == "sell":
            buyer = player
            seller = self
        else:  # action == "buy"
            buyer = self
            seller = player

        # Create and save the trade
        trade = Trade(buyer=buyer, seller=seller, price=price, game_session=game_session)
        trade.save()

        # You can return trade or any information related to the created trade if needed.
        return trade

    
    def decide_bid_offer(self, initial_price, message):
        """
        Decide the AI's bid and offer based on the message and its computed EV.
        """
        current_ev = self.compute_ev(initial_price, message)

        bid = current_ev - (current_ev * AIPlayer.UNCERTAINTY_FACTOR)
        offer = current_ev + (current_ev * AIPlayer.UNCERTAINTY_FACTOR) 

        return bid, offer
    


class Message(models.Model):
    CONTENT_MAX_LENGTH = 255

    content = models.CharField(max_length=CONTENT_MAX_LENGTH)
    IMPACT_TYPES = (
        ('bullish', 'Bullish'),
        ('bearish', 'Bearish'),
    )
    impact_type = models.CharField(max_length=7, choices=IMPACT_TYPES)
    impact_value = models.DecimalField(max_digits=5, decimal_places=2)  # This will allow values like 99.99
    release_timestamp = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.content
    
class GameSession(models.Model):
    players = models.ManyToManyField(Player)
    ai_players = models.ManyToManyField(AIPlayer, related_name='game_sessions')
    active = models.BooleanField(default=True)
    messages = models.ManyToManyField(Message)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    initial_price = models.DecimalField(max_digits=10, decimal_places=2, default=70)
    trade_out_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def finish(self):
        with transaction.atomic():
            self.active = False
            self.finished_at = timezone.now()
            final_price = self.initial_price

            for message in self.messages.all():
                if message.impact_type == "bullish":
                    final_price += final_price * (message.impact_value / 100)
                elif message.impact_type == "bearish":
                    final_price -= final_price * (message.impact_value / 100)

            self.trade_out_price = final_price
            self.save()

    def start_new_round(self):
        #code to start a new round goes here
        pass

    @staticmethod
    def add_player_to_game_session(player, game_session):
    # First, set all other active sessions of this player to inactive
        active_sessions = player.games.filter(active=True)
        for session in active_sessions:
            session.finish()

        # Then, add the player to the new game session
        game_session.players.add(player)
    
    def assign_random_messages(self):
        # Directly fetch 8 random messages
        selected_messages = Message.objects.order_by('?')[:8]

        # Check if we have at least 8 messages
        if len(selected_messages) < 8:
            raise ValueError("Not enough messages in the database to sample from!")

        # Associate these messages with the GameSession
        self.messages.add(*selected_messages)
    
    def save(self, *args, **kwargs):
        # Check if this is a new instance (i.e. being created and not updated)
        is_new = not self.pk
        super(GameSession, self).save(*args, **kwargs)

        # If it's a new instance, assign random messages to it
        if is_new:
            self.assign_random_messages()


class Round(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    start_time = models.DateTimeField(auto_now_add=True)
    end_time = models.DateTimeField(null=True, blank=True)
    round_number = models.IntegerField(default=0)

    def finish(self):
        self.end_time = timezone.now()
        self.save()


class Trade(models.Model):
    game_session = models.ForeignKey(GameSession, on_delete=models.CASCADE)
    buyer = models.ForeignKey(Trader, related_name='buy_trades', on_delete=models.CASCADE)
    seller = models.ForeignKey(Trader, related_name='sell_trades', on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=6, decimal_places=2) # price in USD per tonne
    quantity = models.IntegerField(default=2000)  # Add the 'quantity' field, it is fixed as 2000 metric tonnes for each trade

    def save(self, *args, **kwargs):
        if self.buyer == self.seller:
            raise ValidationError("Buyer and seller can't be the same Trader.")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Trade: {self.buyer.name} bought from {self.seller.name} at {'{:.2f}'.format(self.price)}"
    

