from django.contrib import admin

from .models import GardenPlot, SeedType, UserSeedInventory

admin.site.register(SeedType)
admin.site.register(UserSeedInventory)
admin.site.register(GardenPlot)
