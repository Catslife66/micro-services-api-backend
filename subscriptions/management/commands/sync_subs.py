from django.core.management.base import BaseCommand

from subscriptions.models import SubscriptionPlan

class Command(BaseCommand):

    def handle(self, *args, **options):
        qs = SubscriptionPlan.objects.filter(active=True)
        for obj in qs:
            sub_perms = obj.permissions.all()
            for group in obj.groups.all():
                group.permissions.set(sub_perms)
