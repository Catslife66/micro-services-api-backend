from django.db import models
from django.db.models.signals import post_save
from django.conf import settings
from django.contrib.auth.models import Group, Permission

import helpers.billing

User = settings.AUTH_USER_MODEL

ALLOW_CUSTOM_GROUPS = True


# Plans -> stripe product
class SubscriptionPlan(models.Model):
    name = models.CharField(max_length=20)
    active = models.BooleanField(default=True)
    groups = models.ManyToManyField(Group) # a collection of permissions
    permissions = models.ManyToManyField(Permission, limit_choices_to={"content_type__app_label": "subscriptions", "codename__in": ['basic', 'plus', 'premium']}) # features
    stripe_id = models.CharField(max_length=50, null=True, blank=True)

    class Meta:
        permissions = [
            ('basic', 'Basic Perm'),
            ('plus', 'Plus Perm'),
            ('premium', 'Premium Perm')
        ]

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


class UserSubscription(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    Subscription = models.ForeignKey(SubscriptionPlan, on_delete=models.SET_NULL, null=True, blank=True)
    active = models.BooleanField(default=True)


def user_sub_post_save(sender, instance, *args, **kwargs):
    user_sub_instance = instance
    user = user_sub_instance.user
    subscription_obj = user_sub_instance.subscription
    groups_ids = []
    if subscription_obj is not None:
        groups = subscription_obj.groups.all()
        groups_ids = groups.value_list('id', flat=True)
    if not ALLOW_CUSTOM_GROUPS:
        user.groups.set(groups_ids)
    else:
        subs_qs = SubscriptionPlan.objects.filter(active=True)
        if subscription_obj is not None:
            subs_qs = subs_qs.exclude(id=subscription_obj.id)
        subs_groups = subs_qs.values_list('group__id', flat=True)
        subs_groups_set = set(subs_groups)
        
        current_groups = user.groups.all().value_list('id', flat=True)
        groups_ids_set = set(groups_ids)
        current_groups_set = set(current_groups) - subs_groups_set
        final_groups_ids = list(groups_ids_set | current_groups_set)
        user.groups.set(final_groups_ids)

post_save.connect(user_sub_post_save, sender=UserSubscription)