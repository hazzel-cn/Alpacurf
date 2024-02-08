from django.db import models


class YouTubeChannel(models.Model):
    cid = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255, null=True, blank=True)
    url = models.URLField("URL", null=True, blank=True)

    def __str__(self):
        if self.name is not None:
            return self.name
        else:
            return self.cid

    class Meta:
        verbose_name = "YouTube Channel"
        verbose_name_plural = "YouTube Channels"


class YouTubeVideo(models.Model):
    vid = models.CharField(max_length=255, unique=True)
    url = models.URLField("URL")
    title = models.CharField("Title", max_length=255)
    description = models.TextField("Desc")
    channel = models.ForeignKey(YouTubeChannel, on_delete=models.CASCADE)
    publish_datetime = models.DateTimeField("Publish Datetime")
    transcription = models.TextField("Transcription")

    def __repr__(self):
        return f"{self.title} - {self.channel.name}"

    def __str__(self):
        return self.__repr__()

    class Meta:
        verbose_name = "YouTube Video"
        verbose_name_plural = "YouTube Videos"


class YouTubeAdvice(models.Model):
    video = models.OneToOneField(YouTubeVideo, on_delete=models.CASCADE, unique=True)
    advice = models.TextField("Advice")

    def __repr__(self):
        return f'Advice for "{self.video.title}"'

    def __str__(self):
        return self.__repr__()

    class Meta:
        verbose_name = "YouTube Advice"
        verbose_name_plural = "YouTube Advices"
