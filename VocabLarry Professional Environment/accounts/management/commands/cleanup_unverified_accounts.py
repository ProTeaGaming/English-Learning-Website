from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone


class Command(BaseCommand):
    help = (
        "Delete accounts that never verified their email address (e.g. fake or "
        "mistyped domains where the verification mail bounced). Only touches "
        "accounts that came through the normal signup flow — they must have an "
        "allauth EmailAddress record, none of them verified, never have logged "
        "in, and be older than --days. Staff and superusers are never deleted. "
        "Meant to run periodically (cron / Task Scheduler)."
    )

    def add_arguments(self, parser):
        parser.add_argument('--days', type=int, default=7,
                            help='Delete unverified accounts older than this many days (default: 7)')
        parser.add_argument('--dry-run', action='store_true',
                            help='List the accounts that would be deleted without deleting them')

    def handle(self, *args, **options):
        User = get_user_model()
        cutoff = timezone.now() - timedelta(days=options['days'])
        stale = (
            User.objects
            .filter(is_staff=False, is_superuser=False,
                    last_login__isnull=True,
                    date_joined__lt=cutoff,
                    emailaddress__isnull=False)
            .exclude(emailaddress__verified=True)
            .distinct()
        )
        pks = list(stale.values_list('pk', flat=True))
        if options['dry_run']:
            for user in stale:
                self.stdout.write(f'would delete {user.email} (joined {user.date_joined:%Y-%m-%d})')
            self.stdout.write(f'{len(pks)} unverified account(s) would be deleted')
            return
        # .delete() is not allowed on a .distinct() queryset — go via pks.
        User.objects.filter(pk__in=pks).delete()
        self.stdout.write(self.style.SUCCESS(
            f'deleted {len(pks)} unverified account(s) older than {options["days"]} day(s)'))
