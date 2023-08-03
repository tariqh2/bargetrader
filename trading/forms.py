# forms.py
from django import forms

class BidOfferForm(forms.Form):
    bid = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
    offer = forms.DecimalField(required=False, max_digits=10, decimal_places=2)
