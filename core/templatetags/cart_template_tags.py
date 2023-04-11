from django import template 
from core.models import Order  

register = template.Library()

# here we are rigistering cart_item_count as a filter which takes user as parameter
@register.filter
def cart_item_count(user):
	if user.is_authenticated:
		order_qs = Order.objects.filter(user = user, ordered = False)
	
		if order_qs.exists():
			return order_qs[0].items.count()

	return 0