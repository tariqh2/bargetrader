from django import forms
from django.core.exceptions import ValidationError
from .models import Player, Trader, User, AIPlayer, Trade, GameSession
from django.db.models import Max, Min

class BidOfferForm(forms.Form):
    bid = forms.DecimalField(required=False, max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'placeholder': 'Enter your bid'}),)
    offer = forms.DecimalField(required=False, max_digits=10, decimal_places=2, widget=forms.NumberInput(attrs={'placeholder': 'Enter your offer'}),)

    def clean(self):
        cleaned_data = super().clean()
        
        bid = cleaned_data.get('bid')
        offer = cleaned_data.get('offer')

        # Validate against the market conditions
        self.validate_against_market(bid, offer)
        
        # Validate the bid and offer values against each other
        self.validate_bid_offer_relation(bid, offer)

        return cleaned_data

    def validate_against_market(self, bid, offer):
        highest_bid = AIPlayer.objects.all().aggregate(Max('bid'))['bid__max']
        lowest_offer = AIPlayer.objects.all().aggregate(Min('offer'))['offer__min']

        # If there are no bids or offers in AIPlayer, return without any checks
        if highest_bid is None and lowest_offer is None:
            return

        if bid is not None:
            if lowest_offer is not None and bid >= lowest_offer:
                raise ValidationError("Your bid price cannot be equal to or higher than the lowest offer in the market.")
        
        if offer is not None:
            if highest_bid is not None and offer <= highest_bid:
                raise ValidationError("Your offer price cannot be equal to or lower than the highest bid in the market.")

    def validate_bid_offer_relation(self, bid, offer):
        if bid is not None and offer is not None and bid > offer:
            raise ValidationError("The bid cannot be higher than the offer.")
