from django.core.management.base import BaseCommand

from subscriptions import utils as subs_utils

class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument("--clear-dangling", action="store_true", default=False)
        parser.add_argument("--days-left", default=0, type=int)
        parser.add_argument("--days-ago", default=0, type=int)
        parser.add_argument("--day-start", default=0, type=int)
        parser.add_argument("--day-end", default=0, type=int)

    def handle(self, *args, **options):
        clear_dangling = options.get('clear_dangling')
        days_ago = options.get('days_ago')
        days_left = options.get('days_left')
        day_start = options.get('day_start')
        day_end = options.get('day_end')

        if clear_dangling:
            subs_utils.clear_dangling_subs()
        else:
            subs_utils.refresh_users_subscriptions(
                    days_ago=days_ago,
                    days_left=days_left,
                    day_start=day_start,
                    day_end=day_end,
                    verbose=True
                )