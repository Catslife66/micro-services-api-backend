import stripe
from decouple import config

from helpers.utils import timestamp_to_datetime

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

def create_checkout_session(customer_id, success_url="", cancel_url="",stripe_price_id="", qty=1, mode="subscription"):
    response = stripe.checkout.Session.create(
        customer=customer_id,
        success_url=success_url,
        cancel_url=cancel_url,
        line_items=[{"price": stripe_price_id, "quantity": qty}],
        mode=mode,
        metadata={
            'price_obj_id': stripe_price_id
        }
    )
    return response.url

def get_checkout_session(session_id):
    response = stripe.checkout.Session.retrieve(session_id)
    return response

def get_subscription(subscription_id):
    response = stripe.Subscription.retrieve(subscription_id)
    return response

def get_customer_active_subscriptions(customer_stripe_id):
    response = stripe.Subscription.list(customer=customer_stripe_id, status='active')
    return response

# temporarily use as stripe api docs has error for retriving sub item
def get_subscription_item_data(subscription_id):
    response = get_subscription(subscription_id)
    sub_item = response.get('items').data[0]
    return sub_item

def cancel_subscription(subscription_id, cancel_at_period_end=False):
    if cancel_at_period_end:
        response = stripe.Subscription.modify(subscription_id, cancel_at_period_end=cancel_at_period_end)
    else:
        response = stripe.Subscription.cancel(subscription_id)
    return response

def get_customer_subcription_plan(session_id):
    checkout_session = get_checkout_session(session_id)
    customer_stripe_id = checkout_session.customer # cs_xxx
    subscription_stripe_id = checkout_session.subscription # sub_xxx
    subscription_plan_price_id = get_subscription(subscription_stripe_id).plan.id # price_xxx
    status = get_subscription(subscription_stripe_id).status
    current_period_start = get_subscription_item_data(subscription_stripe_id).current_period_start
    current_period_end = get_subscription_item_data(subscription_stripe_id).current_period_end
    data = {
        'customer_stripe_id': customer_stripe_id, 
        'subscription_plan_price_id': subscription_plan_price_id, 
        'subscription_stripe_id': subscription_stripe_id,
        'status': status,
        'current_period_start': timestamp_to_datetime(current_period_start),
        'current_period_end': timestamp_to_datetime(current_period_end)
    }
    return data


