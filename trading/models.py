from django.db import models
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.db.models import Sum


# Create your models here.

''' 
    Set up a base class called Trader for Player and AIPlayer to inherit. 
'''

class Trader(models.Model):
    name = models.CharField(max_length=200)

    # This method calculates the position by summing all the buy and sell trades

    def calculate_position(self):
        buy_trades = self.buy_trades.all().aggregate(Sum('quantity'))['quantity__sum']
        sell_trades = self.sell_trades.all().aggregate(Sum('quantity'))['quantity__sum']

        # If there are no buy or sell trades, set position to 0
        buy_trades_total = buy_trades if buy_trades else 0
        sell_trades_total = sell_trades if sell_trades else 0

        position = buy_trades_total - sell_trades_total
        return position
    
    # This method calculates the total cash flow for buy and sell trades made by the trader

    def calculate_cash_flow(self):
        cash_flow = 0

        buy_trades = self.buy_trades.all()
        for trade in buy_trades:
            cash_flow -= trade.quantity * trade.price
        
        sell_trades = self.sell_trades.all()
        for trade in sell_trades:
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

class Trade(models.Model):
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
    


