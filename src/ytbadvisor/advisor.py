import os
from typing import List

import requests
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.utils.dateparse import parse_datetime
from django.utils.html import strip_tags
from loguru import logger
from pytube import YouTube

from alpacurf.settings import YOUTUBE_API_KEY, EMAIL_SUBSCRIBERS
from libs.advisor import Advisor
from libs.ai import (
    mp4_to_transcription,
    conclude_with_transcription,
)
from ytbadvisor.models import YouTubeVideo, YouTubeChannel, YouTubeAdvice


class YoutubeAdvisor(Advisor):
    def __init__(self):
        super().__init__()

        logger.info(f"Advisor '{self.__class__.__name__}' initiated")

    def __del__(self) -> None:
        logger.info(f"Advisor '{self.__class__.__name__}' destructed")

    def _find_new_videos(
        self, channel: YouTubeChannel, max_results: int = 10
    ) -> List[YouTubeVideo]:
        """
        Get video URLs and related objects from YouTube channel.
        :param channel:
        :return: list of YouTubeVideo objects
        """
        logger.info(f"Getting video URLs from channel {channel.cid}")

        url = f"https://www.googleapis.com/youtube/v3/search?key={YOUTUBE_API_KEY}&channelId={channel.cid}&part=snippet,id&order=date&maxResults={max_results}"
        resp = requests.get(url)

        videos: List[YouTubeVideo] = []
        items = resp.json()["items"]

        for i in items:
            logger.debug(f"Video info: {i}")

            # Skip the item if it is a Live video
            print()
            if i["snippet"]["liveBroadcastContent"] == "live":
                continue

            vid = i["id"]["videoId"]
            if YouTubeVideo.objects.filter(vid=vid).exists():
                # Collect videos without transcription
                v = YouTubeVideo.objects.get(vid=vid)
                if not v.transcription:
                    logger.info(f"Existing video: {v}")
                    videos.append(v)

            else:
                # New videos
                v = YouTubeVideo(
                    vid=vid,
                    url=f"https://www.youtube.com/watch?v={vid}",
                    title=i["snippet"]["title"],
                    description=i["snippet"]["description"],
                    channel=channel,
                    publish_datetime=parse_datetime(i["snippet"]["publishedAt"]),
                    transcription="",
                )
                logger.info(f"New video: {v.title}")
                videos.append(v)

        for v in videos:
            logger.info(f"Transcribe: {v.title}")
            v.transcription = self._get_transcription(v)
            v.save()

        logger.info(f"Checking {len(videos)} videos: {videos}")
        return videos

    def _summarize_new_videos(self, channel: YouTubeChannel, max_results: int = 3):
        """
        To retrieve videos, get transcriptions, and save them in the database.
        :param channel: Specify the channel
        :return:
        """
        videos = self._find_new_videos(channel, max_results)
        for v in videos:
            if YouTubeAdvice.objects.filter(video_id=v.id).exists():
                continue

            v.save()

            logger.debug(f"Summarizing the transcription: {v}")
            advice = YouTubeAdvice(
                video=v, advice=conclude_with_transcription(v.transcription)
            )
            advice.save()
            logger.debug(advice.advice)

        return True

    @staticmethod
    def _get_transcription(video: YouTubeVideo) -> str:
        """
        Download the video and get the transcription string with OpenAI API speech2text.
        :param video:
        :return:
        """
        ytb = YouTube(video.url)
        audio = ytb.streams.get_audio_only("mp4")

        tmp_audio_filename = "tmp_audio.mp4"
        logger.info(f"Downloading audio: {video.title}")
        audio.download(filename=tmp_audio_filename)

        logger.info(f"Extracting transcription: {video.title}")
        transcription = mp4_to_transcription(tmp_audio_filename, 25, 64)
        os.remove(tmp_audio_filename)
        logger.debug(f"Transcription extracted: {transcription}")

        return transcription

    def advise(self):
        for channel in YouTubeChannel.objects.filter():
            self._summarize_new_videos(channel, 3)

        subject = "[YouTube Advisor] Video Summary"
        analyses = []
        candidate_advices = YouTubeAdvice.objects.filter(notified=False)
        for adv in candidate_advices:
            analyses.append(
                {
                    "time": adv.video.publish_datetime,
                    "content": adv.advice,
                    "source_url": adv.video.url,
                    "source_title": adv.video.title,
                }
            )

        logger.info(f"Advises to be sent: {len(analyses)}")
        if len(analyses) == 0:
            return

        html_content = render_to_string(
            "email.html",
            context={"analyses": analyses},
        ).replace("\n", "<br>")
        text_content = strip_tags(html_content)
        email = EmailMultiAlternatives(subject, text_content, None, EMAIL_SUBSCRIBERS)
        email.attach_alternative(html_content, "text/html")
        email.send()

        # Update the `notified` flag in the database.
        candidate_advices.update(notified=True)
