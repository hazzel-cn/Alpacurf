from django.contrib import admin

from ytbadvisor.models import YouTubeVideo, YouTubeChannel, YouTubeAdvice


@admin.register(YouTubeChannel)
class YouTubeChannelAdmin(admin.ModelAdmin):
    list_display = ("cid", "name", "url")


@admin.register(YouTubeVideo)
class YouTubeVideoAdmin(admin.ModelAdmin):
    list_display = ("url", "title")


@admin.register(YouTubeAdvice)
class YouTubeAdviceAdviceAdmin(admin.ModelAdmin):
    list_display = ("video", "advice")
