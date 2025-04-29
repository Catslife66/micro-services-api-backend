from django.contrib import admin

from .models import SubscriptionPlan, SubscriptionPlanPrice, UserSubscription

class SubscriptionPriceInline(admin.StackedInline):
    model = SubscriptionPlanPrice
    readonly_fields = ['stripe_id']
    extra = 0
    can_delete = False


class SubscriptionAdmin(admin.ModelAdmin):
    inlines = [SubscriptionPriceInline]
    list_display = ['name', 'active', 'stripe_id']
    readonly_fields = ['stripe_id']


admin.site.register(SubscriptionPlan, SubscriptionAdmin)
admin.site.register(UserSubscription)
