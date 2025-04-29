import stripe
from decouple import config

DJANGO_DEBUG = config("DJANGO_DEBUG", cast=bool, default=True)
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', cast=str, default="")

if not DJANGO_DEBUG and 'sk_test' in STRIPE_SECRET_KEY:
    raise ValueError('Invalid stripe key for production')

stripe.api_key = STRIPE_SECRET_KEY

def create_customer(name="", email="", metadata={}):
    response = stripe.Customer.create(
        name=name,
        email=email,
        metadata=metadata
    )
    return response.id

def create_product(name="", metadata={}):
    response = stripe.Product.create(
        name=name,
        metadata=metadata
    )
    return response.id

def create_price(currency="", unit_amout="", interval="", product=None, metadata={}):
    if product is None:
        raise ValueError('Need to be linked to a stripe product.')
    
    response = stripe.Price.create(
        currency=currency,
        unit_amount=unit_amout,
        recurring={'interval': interval},
        product=product,
        metadata=metadata
    )
    return response.id