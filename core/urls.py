from django.urls import path 
from .views import (
	HomeView, 
	ItemDetailView,
	OrderSummaryView,
	CheckoutView,
	PaymentView,
	AddCouponView,
	RefundRequestView,
	add_to_cart,
	remove_from_cart,
	add_one_item_to_cart, 
	remove_one_item_from_cart,
	)

app_name = 'core'

urlpatterns = [
	path('', HomeView.as_view(), name = 'item-list'),
	path('product/<slug:slug>/', ItemDetailView.as_view(), name = 'item-detail'),
	path('add-to-cart/<slug:slug>/', add_to_cart, name='add-to-cart'),
	path('remove-from-cart/<slug:slug>/', remove_from_cart, name = 'remove-from-cart'),
	path('order-summary/', OrderSummaryView.as_view(), name = 'order-summary'),
	path('add-one-item-to-cart/<slug:slug>', add_one_item_to_cart, name = 'add-one-item-to-cart'),
	path('remove-one-item-from-cart/<slug:slug>', remove_one_item_from_cart, name = 'remove-one-item-from-cart'),
	path('checkout/', CheckoutView.as_view(), name = 'checkout'),
	path('payment/<slug:payment_option>/', PaymentView.as_view(), name = 'payment'),
	path('add-coupon/', AddCouponView.as_view(), name = 'add-coupon'),
	path('request-refund/', RefundRequestView.as_view(), name = 'request-refund')
]
