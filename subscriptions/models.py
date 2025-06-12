import datetime
from django.utils import timezone
from django.conf import settings
from django.contrib.auth.models import Group, Permission
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_save

import helpers.billing

User = settings.AUTH_USER_MODEL

ALLOW_CUSTOM_GROUPS = True


# SubscriptionPlans -> stripe product -> prod_xxx
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=20)
    descriptions = models.TextField(null=True, blank=True)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group) # a collection of permissions
    permissions = models.ManyToManyField(
        Permission, 
        limit_choices_to={
            "content_type__app_label": "subscriptions", 
            "codename__in": ['basic', 'plus', 'premium']
        }
    ) # features
    stripe_id = models.CharField(max_length=50, null=True, blank=True)
    order = models.IntegerField(default=-1)
    featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        permissions = [
            ('basic', 'Basic Perm'),
            ('plus', 'Plus Perm'),
            ('premium', 'Premium Perm')
        ]
        ordering = ['order']

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.stripe_id:
            stripe_id = helpers.billing.create_product(
                name=self.name,
                metadata={'subscription_plan_id': self.id}
            )
            self.stripe_id = stripe_id
        super().save(*args, **kwargs)


# subscription price -> stripe price -> price_xxx
class SubscriptionPlanPrice(models.Model):
    class IntervalChoices(models.TextChoices):
        MONTHLY = 'month', 'Monthly'
        YEARLY = 'year', 'Yearly'
    
    subscription_plan = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_id = models.CharField(max_length=50, null=True, blank=True)
    interval = models.CharField(max_length=20, choices=IntervalChoices, default=IntervalChoices.MONTHLY)
    price = models.DecimalField(max_digits=8, decimal_places=2, default=0.01)
    order = models.IntegerField(default=-1)
    featured = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['order', 'featured', '-updated_at']

    @property
    def stripe_product_id(self):
        if not self.subscription_plan:
            return None
        return self.subscription_plan.stripe_id
    
    @property
    def stripe_currency(self):
        return 'gbp'
    
    @property
    def stripe_unit_amount(self):
        return int(self.price * 100)

    def save(self, *args, **kwargs):
        if not self.stripe_id and self.subscription_plan is not None:
            stripe_id = helpers.billing.create_price(
                currency=self.stripe_currency, 
                unit_amout=self.stripe_unit_amount,
                interval=self.interval,
                product=self.stripe_product_id,
                metadata={
                    'subscription_plan_price_id': self.id
                }
            )
            self.stripe_id = stripe_id

        if self.stripe_id and self.subscription_plan.id and self.id: 
            existing_stripe_price = SubscriptionPlanPrice.objects.get(id=self.id)
            if existing_stripe_price.price != self.price:
                raise ValueError('Cannot modify stripe price!')
            
        super().save(*args, **kwargs)

        if self.subscription_plan and self.featured:
            qs = SubscriptionPlanPrice.objects.filter(
                subscription_plan=self.subscription_plan,
                interval=self.interval
            ).exclude(id=self.id)
            qs.update(featured=False)


class UserSubscriptionQuerySet(models.QuerySet):
    def by_range(self, day_start=7, day_end=120):
        now = timezone.now()
        days_start_from_now = now + datetime.timedelta(days=day_start)
        days_end_from_now = now + datetime.timedelta(days=day_end)
        range_start = days_start_from_now.replace(hour=0, minute=0, second=0, microsecond=0)
        range_end = days_end_from_now.replace(hour=23, minute=59, second=59, microsecond=59)
        return self.filter(
            current_period_end__gte=range_start,
            current_period_end__lte=range_end,
        )

    def by_days_left(self, days_left=7):
        now = timezone.now()
        in_n_days = now + datetime.timedelta(days=days_left)
        day_start = in_n_days.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = in_n_days.replace(hour=23, minute=59, second=59, microsecond=59)
        return self.filter(
            current_period_end__gte=day_start,
            current_period_end__lte=day_end,
        )
    
    def by_days_ago(self, days_ago=3):
        now = timezone.now()
        in_n_days = now + datetime.timedelta(days=days_ago)
        day_start = in_n_days.replace(hour=0, minute=0, second=0, microsecond=0)
        day_end = in_n_days.replace(hour=23, minute=59, second=59, microsecond=59)
        return self.filter(
            current_period_end__gte=day_start,
            current_period_end__lte=day_end,
        )

    def by_active_trialing(self):
        active_subs_lookup = (
            Q(status = SubscriptionStatus.ACTIVE) |
            Q(status = SubscriptionStatus.TRIALING)
        )
        return self.filter(active_subs_lookup)
    
    def by_user_ids(self, user_ids=None):
        if isinstance(user_ids, list):
            return self.filter(user_id__in=user_ids)
        elif isinstance(user_ids, int):
            return self.filter(user_id__in=[user_ids])
        return self


class UserSubscriptionManager(models.Manager):
    def get_queryset(self):
        return UserSubscriptionQuerySet(self.model, using=self.db)
    

class SubscriptionStatus(models.TextChoices):
    INCOMPLETE = 'incomplete', 'Incomplete'
    INCOMPLETE_EXPIRED = 'incomplete_expired', 'Incomplete Expired'
    TRIALING = 'trialing', 'Trialing'
    ACTIVE = 'active', 'Active'
    PAST_DUE = 'past_due', 'Past Due'
    CANCELED = 'canceled', 'Canceled'
    UNPAID = 'unpaid', 'Unpaid'
    PAUSED = 'paused', 'Paused'


# user subscription -> stripe customer subcriptions -> sub_xxx
class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    stripe_id = models.CharField(max_length=50, null=True, blank=True)
    active = models.BooleanField(default=True)
    original_period_start = models.DateTimeField(auto_now_add=False, auto_now=False, null=True, blank=True)
    current_period_start = models.DateTimeField(auto_now_add=False, auto_now=False, null=True, blank=True)
    current_period_end = models.DateTimeField(auto_now_add=False, auto_now=False, null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=SubscriptionStatus, null=True, blank=True)
    is_cancelled = models.BooleanField(default=False)
    cancelled_at = models.DateTimeField(auto_now_add=False, auto_now=False, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def billing_cycle_anchor(self):
        """
        delay a new subscription until the current subscription runs out
        """
        if not self.current_period_end:
            return None
        return int(self.current_period_end.timestamp())
    
    @property
    def is_allow_to_cancel(self):
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]

    def save(self, *args, **kwargs):
        if self.original_period_start is None and self.current_period_start is not None:
            self.original_period_start = self.current_period_start
        super().save(*args, **kwargs)


def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.values_list('id', flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
    else:
        subs_qs = SubscriptionPlan.objects.filter(active=True)
        if subscription_obj is not None:
            subs_qs = subs_qs.exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list('groups__id', flat=True)
        subs_groups_set = set(subs_groups)
        
        current_groups = user.groups.all().values_list('id', flat=True)
        groups_ids_set = set(groups_ids)
        current_groups_set = set(current_groups) - subs_groups_set
        final_groups_ids = list(groups_ids_set | current_groups_set)
        user.groups.set(final_groups_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)