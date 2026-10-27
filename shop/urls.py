from django.urls import path

from .views import BuyItemView, ShopItemListView

urlpatterns = [
    path('', ShopItemListView.as_view(), name='shop-list'),
    path('<int:item_id>/buy/', BuyItemView.as_view(), name='shop-buy'),
]
