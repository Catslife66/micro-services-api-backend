import stripe
from decouple import config

DJANGO_DEBUG = config("DJANGO_DEBUG", cast=bool, default=True)
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', cast=str, default="")

if not DJANGO_DEBUG and 'sk_test' in STRIPE_SECRET_KEY:
    raise ValueError('Invalid stripe key for production')

stripe.api_key = STRIPE_SECRET_KEY

def create_custome(name="", email="", metadata={}):
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