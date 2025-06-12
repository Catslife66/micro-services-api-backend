from django.http import JsonResponse
from django.conf import settings
from django.shortcuts import get_object_or_404
from ninja_extra import api_controller, route
from ninja_jwt.authentication import JWTAuth

from auth_service.models import AppUser
from customers.models import Customer
import helpers.billing
from payments.schemas import CheckoutSessionIn
from subscriptions.models import SubscriptionPlan, SubscriptionPlanPrice, UserSubscription


@api_controller('/payments', tags=['Payments'])
class PaymentController:
    @route.post('/create-checkout-session', auth=[JWTAuth()])
    def create_checkout_session(self, payload:CheckoutSessionIn):
        user = get_object_or_404(AppUser, email=payload.useremail)
        price_obj = get_object_or_404(SubscriptionPlanPrice, stripe_id=payload.price_id)
        customer_obj, _ = Customer.objects.get_or_create(user=user)

        url_prefix = settings.CORS_ALLOWED_ORIGINS[0]
        success_url = f"{url_prefix}/checkout/success" +"?session_id={CHECKOUT_SESSION_ID}"
        cancel_url = f"{url_prefix}/pricing"
        response = helpers.billing.create_checkout_session(
            customer_id=customer_obj.stripe_id, 
            success_url=success_url, 
            cancel_url=cancel_url,
            stripe_price_id=price_obj.stripe_id
        )
        return response
    

    @route.get('/checkout-success/{str:session_id}')
    def checkout_session_success(self, session_id: str):
        data = helpers.billing.get_customer_subcription_plan(session_id)
        
        try:
            subscription_obj = SubscriptionPlan.objects.get(subscriptionplanprice__stripe_id=data.get('subscription_plan_price_id'))
        except:
            subscription_obj = None

        try:
            user_obj = AppUser.objects.get(customer__stripe_id=data.get('customer_stripe_id'))
        except:
            user_obj = None
        
        user_sub_obj_exists = False
        user_sub_data = {
            "subscription": subscription_obj,
            "stripe_id": data.get('subscription_stripe_id'), 
            "is_cancelled": False,
            "current_period_start": data.get('current_period_start'),
            "current_period_end": data.get('current_period_end'),
            "status": data.get('status')
        }
        try:
            user_sub_obj = UserSubscription.objects.get(user=user_obj)
            user_sub_obj_exists = True
        except UserSubscription.DoesNotExist:
            user_sub_obj = UserSubscription.objects.create(user=user_obj, **user_sub_data)
        except: 
            user_sub_obj = None
      
        if None in [subscription_obj, user_obj, user_sub_obj]:
            return JsonResponse({"isSuccess": False, "error": "Something went wrong with subscription models."})
        
        if user_sub_obj_exists:
            # cancel old sub
            old_subscription_stripe_id = user_sub_obj.stripe_id
            is_same_stripe_id = old_subscription_stripe_id == data.get('subscription_stripe_id')
            if old_subscription_stripe_id is not None and not is_same_stripe_id:
                try:
                    helpers.billing.cancel_subscription(old_subscription_stripe_id)
                except:
                    pass
            # assign new sub
            for k, v in user_sub_data.items():
                setattr(user_sub_obj, k, v)
            user_sub_obj.save()
        
        return JsonResponse({"isSuccess": True, "message": "Thank you for your subscription."})

