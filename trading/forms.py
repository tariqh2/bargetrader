# forms.py
from django import forms
from django.core.exceptions import ValidationError
from .models import Player, Trader, User, AIPlayer, Trade, GameSession
from django.db.models import Max, Min


class BidOfferForm(forms.Form):
    bid = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    offer = forms.DecimalField(required=False, max_digits=10, decimal_places=2)

    def clean(self):
        cleaned_data = super().clean()

        # calculate the highest bid and lowest offer in the market
        highest_bid = AIPlayer.objects.all().aggregate(Max('bid'))['bid__max']
        lowest_offer = AIPlayer.objects.all().aggregate(Min('offer'))['offer__min']

        # apply validation rules
        if cleaned_data.get('bid') is not None and cleaned_data.get('bid') >= lowest_offer:
            raise ValidationError("Your bid price cannot be equal to or higher than the lowest offer in the market.")

        if cleaned_data.get('offer') is not None and cleaned_data.get('offer') <= highest_bid:
            raise ValidationError("Your offer price cannot be equal to or lower than the highest bid in the market.")