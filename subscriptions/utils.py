from django.db.models import Q

from customers.models import Customer
from .models import SubscriptionStatus, UserSubscription, SubscriptionPlan, SubscriptionPlanPrice   
import helpers.billing


def sync_sub_groups_permisstion():
    qs = SubscriptionPlan.objects.filter(active=True)
    for obj in qs:
        sub_perms = obj.permissions.all()
        for group in obj.groups.all():
            group.permissions.set(sub_perms)

def refresh_users_subscriptions(
        user_ids=None,
        active_only=True,
        days_ago=0,
        days_left=0,
        day_start=0,
        day_end=0,
        verbose=False,
    ):

    qs = UserSubscription.objects.all()
    if active_only:
        qs = qs.by_active_trialing()
    if user_ids is not None:
        qs = qs.by_user_ids(user_ids=user_ids)
    if days_ago > 0:
        qs = qs.by_days_ago(days_ago=days_ago)
    if days_left > 0:
        qs = qs.by_days_left(days_left=days_left)
    if day_start > 0 and day_end > 0:
        qs = qs.by_range(day_start=day_start, day_end=day_end)
    for obj in qs:
        if obj.stripe_id:
            sub_data = helpers.billing.get_subscription(obj.stripe_id)
            sub_price = SubscriptionPlanPrice.objects.get(stripe_id=sub_data.plan.id)
            sub_obj = {
                'id': obj.id,
                'subscription' : obj.subscription.name,
                'stripe_id': obj.stripe_id,
                'status': obj.status,
                'price' : sub_price.price,
                'interval' : sub_price.interval,
                'created_at' : obj.created_at,
                'current_period_start' : obj.current_period_start,
                'current_period_end': obj.current_period_end,
                'is_allow_to_cancel': obj.is_allow_to_cancel,
                'is_cancelled': obj.is_cancelled,
                'cancelled_at': obj.cancelled_at
            }
            for k, v in sub_obj.items():
                setattr(obj, k, v)
            obj.save()

def clear_dangling_subs():
    qs = Customer.objects.filter(stripe_id__isnull=False)
    for customer_obj in qs:
        user = customer_obj.user
        customer_stripe_id = customer_obj.stripe_id
        print(f'sync {user} - {customer_stripe_id} subs and remove old ones')
        subs = helpers.billing.get_customer_active_subscriptions(customer_stripe_id)

        for sub in subs:
            existing_user_subs_qs = UserSubscription.objects.filter(stripe_id__iexact=f'{sub.id}')
            if existing_user_subs_qs:
                continue
            helpers.billing.cancel_subscription(sub.id, cancel_at_period_end=True)