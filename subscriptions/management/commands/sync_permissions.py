from django.core.management.base import BaseCommand

from subscriptions import utils as subs_utils

class Command(BaseCommand):

    def handle(self, *args, **options):
        subs_utils.sync_sub_groups_permisstion()