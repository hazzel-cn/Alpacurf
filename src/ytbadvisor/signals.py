import requests
from django.db.models.signals import post_save
from django.dispatch import receiver

from alpacurf.settings import YOUTUBE_API_KEY
from ytbadvisor.models import YouTubeChannel


@receiver(post_save, sender=YouTubeChannel)
def retrieve_channel_info(sender, instance, created, **kwargs):
    # Set URL and name for the channel
    if instance.name is None or instance.url is None:
        url = f"https://youtube.googleapis.com/youtube/v3/channels?part=snippet&id=UCQI_bOZmTFM1LfiVXWg6EzQ&key={YOUTUBE_API_KEY}"
        resp = requests.get(url)
        instance.name = resp.json()["items"][0]["snippet"]["title"]
        instance.url = f"https://www.youtube.com/channel/{instance.cid}"
        instance.save()
