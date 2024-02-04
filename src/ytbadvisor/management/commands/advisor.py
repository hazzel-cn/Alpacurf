from django.core.management.base import BaseCommand

from ytbadvisor.advisor import YoutubeAdvisor


class Command(BaseCommand):
    help = "Closes the specified poll for voting"

    def handle(self, *args, **options):
        advisor = YoutubeAdvisor()
        advisor.advise()
