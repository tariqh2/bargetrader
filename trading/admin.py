from django.contrib import admin
from .models import Trader, Player, AIPlayer, Trade

# Register your models here.
admin.site.register(Trader)
admin.site.register(Player)
admin.site.register(AIPlayer)
admin.site.register(Trade)
