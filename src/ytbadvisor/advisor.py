import os
from typing import List

import requests
from loguru import logger
from pytube import YouTube

from alpacurf.settings import YOUTUBE_API_KEY
from libs.advisor import Advisor
from libs.ai import (
    mp4_to_transcription,
    conclude_with_transcription,
)
from ytbadvisor.models import YouTubeVideo, YouTubeChannel, YouTubeAdvice


class YoutubeAdvisor(Advisor):
    def __init__(self):
        super().__init__()

    @staticmethod
    def _get_videos_from_channel(
        channel: YouTubeChannel, max_results: int = 10
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
            vid = i["id"]["videoId"]
            if YouTubeVideo.objects.filter(vid=vid).exists():
                break
            v = YouTubeVideo(
                vid=vid,
                url=f"https://www.youtube.com/watch?v={vid}",
                title=i["snippet"]["title"],
                description=i["snippet"]["description"],
                channel=channel,
                publish_datetime=i["snippet"]["publishedAt"],
                transcription="",
            )

            logger.debug(f"Found video {v}")
            videos.append(v)

        logger.info(f"Found new {len(videos)} videos: {videos}")
        return videos

    def _retrieve_video_data_to_db(self, channel: YouTubeChannel, max_results: int = 3):
        """
        To retrieve videos, get transcriptions, and save them in the database.
        :param channel: Specify the channel
        :return:
        """
        videos = self._get_videos_from_channel(channel, max_results)
        for v in videos:
            v.channel = channel

            logger.info(f"Getting transcription: {v}")
            v.transcription = self._get_transcription(v)
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
        logger.debug(f"Downloading audio")
        audio.download(filename=tmp_audio_filename)

        logger.debug(f"Extracting transcription")
        transcription = mp4_to_transcription(tmp_audio_filename)
        os.remove(tmp_audio_filename)
        logger.debug(f"Transcription extracted: {transcription}")

        return transcription

    def advise(self):
        for channel in YouTubeChannel.objects.filter():
            self._retrieve_video_data_to_db(channel, 1)
