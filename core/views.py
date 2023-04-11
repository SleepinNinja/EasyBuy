from django.shortcuts import render, get_object_or_404, redirect
from .models import Item, OrderItem, Order, Address, Payment, Coupon, Refund
from django.views.generic import ListView, DetailView, View
from django.db.models import F
from django.utils import timezone
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.edit import FormView, CreateView
from .forms import CheckoutForm, CouponForm, RefundForm
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse_lazy
from django.conf import settings
import stripe 
import random
import string

def is_valid_form(values):
	valid = True 

	for field in values:
		if field == '':
			valid = False 

	return valid


def create_ref_code():
	return ''.join(random.choices(string.ascii_lowercase + string.digits, k = 20))


def get_object(request, model, model_filter, message, redirect_to, redirect_param = None):
	try:
		obj = model.objects.get(**model_filter)

	except ObjectDoesNotExist:
		messages.info(request, message)

		if redirect_param:
			return redirect(redirect_to, redirect_param)

		return redirect(redirect_to)

	else:
		return obj


class HomeView(ListView):
	model = Item 
	template_name = 'home.html'
	paginate_by = 10
	context_object_name = 'items'
 

class OrderSummaryView(LoginRequiredMixin, View):
	def get(self, *args, **kwargs):
		order = Order.objects.filter(user = self.request.user, ordered = False)
		
		if order.exists():
			order = order[0]
			context = {
				'order': order,
			}
			return render(self.request, 'order_summary.html', context)
		
		else:
			messages.info(self.request, 'You dont have any items to order')
			return redirect('/')


class ItemDetailView(DetailView):
	"""
	Detail view takes pk or slug from the url and gets the specified 
	object from database.
	"""
	model = Item 
	template_name = 'product.html'
	context_object_name = 'item'


class CheckoutView(LoginRequiredMixin, FormView):
	template_name = 'checkout.html'
	form_class = CheckoutForm 

	def get_context_data(self, *args, **kwargs):
		context = super().get_context_data(*args, **kwargs)
		order_qs = Order.objects.filter(user = self.request.user, ordered = False)
		
		if order_qs.exists():
			context['order'] = order_qs[0]

		context['coupon_form'] = CouponForm()
		context['COUPON_FORM'] = True

		shipping_address_qs = Address.objects.filter(user = self.request.user, address_type = 'B', default = True)

		if shipping_address_qs.exists():
			context['default_shipping_address'] = shipping_address_qs[0]

		billing_address_qs = Address.objects.filter(user = self.request.user, address_type = 'S', default = True)
		
		if billing_address_qs.exists():
			context['default_billing_address'] = billing_address_qs[0]
			
		return context

	def form_valid(self, form):
		order_qs = Order.objects.filter(user = self.request.user, ordered = False)
		print(form.cleaned_data)
		if order_qs.exists():
			order = order_qs[0]
			use_default_shipping = form.cleaned_data.get('use_default_shipping')
			use_default_billing = form.cleaned_data.get('use_default_billing')
			
			if use_default_shipping:
				print('using default shipping_address')
				default_shipping_address_qs = Address.objects.filter(user = self.request.user, address_type = 'S', default = True)
				
				if default_shipping_address_qs.exists():
					shipping_address = default_shipping_address_qs[0]
					order.shipping_address = shipping_address

				else:
					messages.info(self.request, 'You dont have a default shipping address')
					return redirect('core:checkout')

			else:
				print('User is entering a new shipping address')
				shipping_address1 = form.cleaned_data.get('shipping_address')
				shipping_address2 = form.cleaned_data.get('shipping_address2')
				shipping_country = form.cleaned_data.get('shipping_country')
				shipping_zip = form.cleaned_data.get('shipping_zip')

				print(shipping_address1, shipping_address2, shipping_country, shipping_zip)

				if is_valid_form([shipping_address1, shipping_country, shipping_zip]):
					shipping_address = Address.objects.create(
						user = self.request.user,
						street_address = shipping_address1,
						appartment_address = shipping_address2,
						country = shipping_country,
						zip_code = shipping_zip,
						address_type = 'S',
					)

					set_default_shipping = form.cleaned_data.get('set_default_shipping')

					if set_default_shipping:
						shipping_address.default = True

					shipping_address.save()
					order.shipping_address = shipping_address

				else:
					messages.info(self.request, 'Please fill in reqired shipping address fields')
			
			
			order.save()

			same_billing_address = form.cleaned_data.get('same_billing_address')

			if same_billing_address:
				billing_address = shipping_address
				billing_address.pk = None 
				billing_address.save()
				billing_address.address_type = 'B'
				billing_address.save()
				order.billing_address = billing_address

			elif use_default_billing:
				print('using default billing address')
				default_billing_address_qs = Address.objects.filter(user = self.request.user, address_type = 'B', default = True)
				
				if default_billing_address_qs.exists():
					billing_address = default_billing_address_qs[0]
					order.billing_address = billing_address

				else:
					messages.info(self.request, 'You dont have a default billing address')
					return redirect('core:checkout')
			else:
				print('user is entering a new billing address')
				billing_address1 = form.cleaned_data.get('billing_address')
				billing_address2 = form.cleaned_data.get('billing_address2')
				billing_country = form.cleaned_data.get('billing_country')
				billing_zip = form.cleaned_data.get('billing_zip')

				if is_valid_form([billing_address1, billing_country, billing_zip]):
					billing_address = Address.objects.create(
						user = self.request.user,
						street_address = billing_address1,
						appartment_address = billing_address2,
						country = billing_country,
						zip_code = billing_zip,
						address_type = 'B',
					)

					set_default_billing = form.cleaned_data.get('set_default_billing')

					if set_default_billing:
						billing_address.default = True

					billing_address.save()
					order.billing_address = billing_address



				else:
					messages.info(self.request, 'Please fill in the required billing address fields')
			
			order.save()

			payment_option = form.cleaned_data.get('payment_option')

			if payment_option == 'S':
				return redirect('core:payment', payment_option = 'stripe')

			elif payment_option == 'P':
				return redirect('core:payment', payment_option = 'paypal')
			
			else:
				messages.info('Invalid payment option selected')
				return redirect('core:checkout')
		
		else:
			messages.info(self.request, 'Order does not exits')
			return redirect('core:checkout')	
	
	def form_invalid(self, form):
		messages.warning(self.request, 'Falied Checkout')
		return redirect('core:checkout')


class PaymentView(View):
	def get(self, *args, **kwargs):
		order = Order.objects.get(user = self.request.user, ordered = False)
		
		if not order.billing_address:
			messages.warning(self.request, 'You do not have a billing address')
			return redirect('core:checkout')
		
		#context = {}
		context = {
			'STRIPE_PUBLISH_KEY': settings.STRIPE_PUBLISH_KEY,
			'order': order,
			'COUPON_FORM': False,
		}

		return render(self.request, 'payment.html', context)

	def post(self, *args, **kwargs):
		token = self.request.POST.get('stripeToken')
		order = Order.objects.get(user = self.request.user, ordered = False)
		amount = int(order.get_total_price() * 100)
		stripe.api_key = settings.STRIPE_SECRET_KEY

		try:
	  		charge = stripe.PaymentIntent.create( 
  				amount = amount,
  				currency = 'usd',
  				payment_method_types = ['card'],
  			)

  			print(charge)

  			order.ordered = True
  			
  			payment = Payment()
  			payment.stripe_charge_id = charge['id']
  			payment.user = self.request.user
  			payment.amount = amount
  			payment.save()
  			
  			order.payment = payment
  			order.ref_code = create_ref_code()
  			order.save()
  			
  			messages.success(self.request, 'Your order was successful!')
  			return redirect('/')

		except stripe.error.CardError as e:
			print('Status is: %s' % e.http_status)
			print('Code is: %s' % e.code)
			print('Param is: %s' % e.param)
			print('Message is: %s' % e.user_message)

			messages.error(self.request, e.user_message)
			return redirect('/')	
		
		except stripe.error.RateLimitError as e:
			messages.error(self.request, 'Rate limit error')
			return redirect('/')		

		except stripe.error.InvalidRequestError as e:
			messages.error(self.request, f'Invalid parameter {e}')
			return redirect('/')

		except stripe.error.AuthenticationError as e:
			messages.error(self.request, 'Authentication Error')
			return redirect('/')

		except stripe.error.APIConnectionError as e:
			messages.error(self.request, 'Network Error')
			return redirect('/')

		except stripe.error.StripeError as e:
			messages.error(self.request, 'Something went wrong. You were not charged please try again later.')
			return redirect('/')

		except Exception as e:
			messages.error(self.request, f'Something is wrong with you implementation {e}')
			return redirect('/')


class AddCouponView(View):
	# as only post method is defined we cannot make a get request to this view
	def post(self, *args, **kwargs):
		coupon_form = CouponForm(request.POST or None)

		if coupon_form.is_valid():
			coupon_code = coupon_form.cleaned_data.get('coupon_code')
			order = get_object(self.request, model = Order, 
				model_filter = {
					'user': request.user, 
					'ordered': False
				},
				message = 'You dont have an active order',
				redirect_to = 'core:item-list',
			)

			coupon = get_object(self.request, model = Coupon, 
				model_filter = {
					'code': coupon_code,
				},
				message = 'Coupon does not exists',
				redirect_to = 'core:checkout',
			)

			order.coupon = coupon
			order.save()

			messages.success(request, 'Successfully added coupon')
			return redirect('core:checkout')

		else:
			messages.info(request, 'Invalid Coupon code')
			return redirct('core:checkout')


class RefundRequestView(View):
	def post(self, *args, **kwargs):
		refund_form = RefundForm(self.request.POST)

		if refund_form.is_valid():
			try: 
				order = Order.objects.get(ref_code = refund_form.cleaned_data.get('ref_code'))

			except ObjectDoesNotExist:
				messages.error(self.request, 'Order with given referene code does not exists')
				return redirect('core:request-refund')

			else:
				order.refund_requested = True 
				order.save()

				message = refund_form.cleaned_data.get('message')
				email = refund_form.cleaned_data.get('email')
				refund = Refund.objects.create(order = order, reason = message, email = email)

				messages.info(self.request, 'Your request for refund is recieved')
				return redirect('/')

		else:
			messages.error(self.request, 'Invalid reference code')
			return redirect('core:request-refund')

	def get(self, *args, **kwargs):
		refund_form = RefundForm()

		context = {
			'refund_form': refund_form
		} 

		return render(self.request, 'request_refund.html', context)


@login_required
def add_to_cart(request, slug):
	# item, created =  orderedModel.objects.get_or_create() gets the item if it exists else create it.
	# the above method returns a tuple.
	# we can use update method on a queryset but then we need to loop through and save each item.
	item = get_object_or_404(Item, slug = slug)
	order_qs = Order.objects.filter(user = request.user, ordered = False)

	if order_qs.exists():
		order = order_qs[0]

		if order.items.filter(item__slug = item.slug).exists():
			order_item = order.items.filter(item__slug = item.slug)[0]
			order_item.quantity = F('quantity') + 1 
			order_item.save()
			messages.info(request, 'This item quantity is updated')

		else:
			order_item = OrderItem.objects.create(item = item) 
			order.items.add(order_item)
			messages.info(request, 'This item is added to you cart')

	else:
		order = Order.objects.create(user = request.user, ordered_date = timezone.now())
		order_item = OrderItem.objects.create(item = item)
		order.items.add(order_item)

	return redirect('core:item-detail', slug = slug)


@login_required
def remove_from_cart(request, slug):
	item = get_object_or_404(Item, slug = slug)
	order_qs = Order.objects.filter(user = request.user, ordered = False)

	if order_qs.exists():
		order = order_qs[0]

		if order.items.filter(item__slug = item.slug).exists():
			order_item = order.items.filter(item = item)[0]
			order.items.remove(order_item)
			order_item.delete()
			messages.info(request, 'This item is removed from you cart')
			return redirect('core:order-summary')

		else:
			messages.info(request, 'This item is not in your cart')
			return redirect('core:product', kwargs = slug)

	else:
		messages.info(request, 'The user do not have an active order')
		
	return redirect('core:item-detail', slug = slug)


@login_required
def remove_one_item_from_cart(request, slug):
	item = get_object_or_404(Item, slug = slug)
	order_qs = Order.objects.filter(user = request.user, ordered = False)

	if order_qs.exists():
		order = order_qs[0]
		order_item_qs = order.items.filter(item = item)

		if order_item_qs.exists():
			order_item = order_item_qs[0]
			order_item.quantity = F('quantity') - 1 
			order_item.save()
			order_item.refresh_from_db()

			print('quantity', order_item.quantity)
			
			if order_item.quantity == 0:
				order.items.remove(order_item)
				order_item.delete()
			
			return redirect('core:order-summary')

		else:
			messages.info(request, 'You dont have this item in your order')

	else:
		messages.info(request, 'You dont have an active order')	 


@login_required
def add_one_item_to_cart(request, slug):
	item = get_object_or_404(Item, slug = slug)
	order_qs = Order.objects.filter(user = request.user, ordered = False)

	if order_qs.exists():
		order = order_qs[0]
		order_item_qs = order.items.filter(item = item)

		if order_item_qs.exists():
			order_item = order_item_qs[0]
			order_item.quantity = F('quantity') + 1
			order_item.save() 
			return redirect('core:order-summary')

		else:
			messages.info(request, 'You dont have this item in your order')

	else:
		messages.info(request, 'You dont have an active order')


