from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget
from django.core.exceptions import ValidationError

PAYMENT_CHOICES = (
	('S', 'Stripe'),
	('P', 'PayPal')
)

class CheckoutForm(forms.Form):
	"""
	def clean(self):
		cleaned_data = super().clean()
		print(cleaned_data)
		default_shipping = cleaned_data.get('use_default_shipping')
		default_billing = cleaned_data.get('use_default_shipping')
		
		if default_shipping:
			billing_fields = ['billing_address', 'billing_address2', 'billing_country', 'billing_zip']
			
			for field in billing_fields:
				if cleaned_data.get(field) == '':
					raise forms.ValidationError(
						'%(field)s cannot be an empty',
						code = 'required',
						params = {'field': ' '.join(field.split('_'))}
					) 

		if default_billing:
			shipping_fields = ['shipping_address', 'shipping_address2', 'shipping_country', 'shipping_zip']
			
			for field in billing_fields:
				if cleaned_data.get(field) == '':
					raise ValidationError(
						'%(field)s cannot be an empty',
						code = 'required',
						params = {'field': ' '.join(field.split('_'))}
					) 

		if not default_billing and not default_shipping:
			#print(cleaned_data)
			for field in cleaned_data:
				if cleaned_data.get(field) == '':
					raise ValidationError(
						'%(field)s cannot be an empty',
						code = 'required',
						params = {'field': ' '.join(field.split('_'))}
					) 
				
	

	def validate_shipping_address(value):
		print(value, 'running validator')
		if value == '':
			raise ValidationError(
				'%(value)s cannot be empty',
				code = 'required',
				params = {'value': value}
			)
	"""
	shipping_address = forms.CharField(required = False)
	shipping_address2 = forms.CharField(required = False)
	shipping_country = CountryField(blank_label = 'Select country').formfield(required = False, widget = CountrySelectWidget(attrs = {'class': 'custom-select d-block w-100'}))
	shipping_zip = forms.CharField(required = False)
	same_shipping_address = forms.BooleanField(required = False)
	set_default_shipping = forms.BooleanField(required = False)
	use_default_shipping = forms.BooleanField(required = False)

	billing_address = forms.CharField(required = False)
	billing_address2 = forms.CharField(required = False)
	billing_country = CountryField(blank_label = 'Select country').formfield(required = False, widget = CountrySelectWidget(attrs = {'class': 'custom-select d-block w-100'}))
	billing_zip = forms.CharField(required = False)
	set_default_billing = forms.BooleanField(required = False)
	use_default_billing = forms.BooleanField(required = False)

	save_info = forms.BooleanField(widget = forms.CheckboxInput(), required = False)
	payment_option = forms.ChoiceField(widget = forms.RadioSelect(), choices = PAYMENT_CHOICES)


class CouponForm(forms.Form):
	coupon_code = forms.CharField(max_length = 20, widget = forms.TextInput({'placeholder': 'Promo Code', 'class': 'form-control'}))


class RefundForm(forms.Form):
	ref_code = forms.CharField(max_length = 20)
	message = forms.CharField(widget = forms.Textarea(attrs = {'rows': 4}))
	email = forms.EmailField(error_messages = {'invalid': 'Please Enter a valid email', 'required': 'Please enter an email address'})