
from django.conf import settings
from django.contrib.sessions.models import Session
from django.core.management.commands.runserver import (
    Command as RunserverCommand,
)


class Command(RunserverCommand):
    def inner_run(self, *args, **options):
        if settings.DEBUG:
            Session.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(
                    "Sesi login lama dihapus untuk development."
                )
            )

        super().inner_run(*args, **options)
