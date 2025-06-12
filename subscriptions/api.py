from typing import List
from urllib import response
from django.http import JsonResponse
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

import helpers.billing
from helpers.utils import timestamp_to_datetime
from .models import SubscriptionPlan, SubscriptionPlanPrice, SubscriptionStatus, UserSubscription
from .schemas import SubscriptionPlanOutSchema, UserCancelSubscriptionErrorSchema, UserCancelSubscriptionSchema, UserSubscriptionSchema


@api_controller('/subscriptions', tags=['Subscription'])
class SubscriptionController:
    @route.get('/', response=List[SubscriptionPlanOutSchema])
    def get_subscription_plans(self):
        obj_list = []
        qs = SubscriptionPlan.objects.filter(active=True, featured=True)
        for obj in qs:
            plan_prices = obj.subscriptionplanprice_set.filter(featured=True)
            obj_list.append({
                "id": obj.id,
                "name": obj.name,
                "descriptions": obj.descriptions,
                "prices": [
                    { 
                        "id": p.id,
                        "price": p.price,
                        "interval": p.interval,
                        "stripe_id": p.stripe_id
                    } for p in plan_prices
                ],
                "stripe_id": obj.stripe_id
            })
        return obj_list
    
    @route.get('/myplans', response=List[UserSubscriptionSchema], auth=[JWTAuth()])
    def get_user_subscription(self, request):
        user = request.user
        try:
            sub_qs = UserSubscription.objects.filter(user=user)
        except:
            sub_qs = None
        user_sub_qs = []
        for obj in sub_qs:
            stripe_sub = helpers.billing.get_subscription(obj.stripe_id)
            sub_price = SubscriptionPlanPrice.objects.get(stripe_id=stripe_sub.plan.id)
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
            print('print end', obj.current_period_end)
            user_sub_qs.append(sub_obj)
        return user_sub_qs

    @route.post('/cancel', response={200: UserCancelSubscriptionSchema, 400: UserCancelSubscriptionErrorSchema}, auth=[JWTAuth()])
    def cancel_user_subscription(self, payload: UserCancelSubscriptionSchema):
        print(payload)
        try:
            sub = UserSubscription.objects.get(stripe_id=payload.stripe_id)
            if not sub.is_allow_to_cancel:
                return 400, {'error': 'This subscription cannot be cancel.'}
            res = helpers.billing.cancel_subscription(sub.stripe_id, payload.cancel_at_period_end)
            sub.status = res.status
            sub.is_cancelled = True
            sub.cancelled_at = timestamp_to_datetime(res.canceled_at)
            sub.save()
            return JsonResponse({'isCanceled': True})

        except Exception as e:
            return 400, {'error': str(e)}