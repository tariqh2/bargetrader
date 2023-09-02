from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum
from django.utils import timezone



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

    def __str__(self):
        return f"AI Player: {self.name}, Style: {self.style}"
    
class GameSession(models.Model):
    players = models.ManyToManyField(Player)
    ai_players = models.ManyToManyField(AIPlayer, related_name='game_sessions')
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    trade_out_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def finish(self):
        self.active = False
        self.finished_at = timezone.now()
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
    

class Message(models.Model):
    CONTENT_MAX_LENGTH = 255

    content = models.CharField(max_length=CONTENT_MAX_LENGTH)
    IMPACT_TYPES = (
        ('bullish', 'Bullish'),
        ('bearish', 'Bearish'),
    )
    impact_type = models.CharField(max_length=7, choices=IMPACT_TYPES)
    impact_value = models.DecimalField(max_digits=5, decimal_places=2)  # This will allow values like 99.99

    def __str__(self):
        return self.content