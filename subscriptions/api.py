from typing import List
from ninja_extra import api_controller, route

from .models import SubscriptionPlan
from .schemas import SubscriptionPlanOutSchema


@api_controller('/subscriptions', tags=['Subscription'])
class SubscriptionController:
    @route.get('/', response=List[SubscriptionPlanOutSchema])
    def get_subscription_plans(self,):
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