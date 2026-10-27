from django.urls import path

from .views import (DigPlotView, FeedPlotView, GardenListView, MicrobePlotView, PlantPhotoView,
                    PlantSeedView, SeedInventoryView, SpeciesListView, SunlightPlotView, WaterPlotView)

urlpatterns = [
    path('', GardenListView.as_view(), name='garden-list'),
    path('species/', SpeciesListView.as_view(), name='species-list'),
    path('seeds/', SeedInventoryView.as_view(), name='seed-inventory'),
    path('<int:slot_index>/plant/', PlantSeedView.as_view(), name='plot-plant'),
    path('<int:slot_index>/water/', WaterPlotView.as_view(), name='plot-water'),
    path('<int:slot_index>/sunlight/', SunlightPlotView.as_view(), name='plot-sunlight'),
    path('<int:slot_index>/feed/', FeedPlotView.as_view(), name='plot-feed'),
    path('<int:slot_index>/microbes/', MicrobePlotView.as_view(), name='plot-microbes'),
    path('<int:slot_index>/plant-photo/', PlantPhotoView.as_view(), name='plot-plant-photo'),
    path('<int:slot_index>/dig/', DigPlotView.as_view(), name='plot-dig'),
]
