import math
import os
import shutil

import ffmpeg
from loguru import logger
from openai import OpenAI
from yaml import safe_load

from alpacurf.settings import BASE_DIR
from alpacurf.settings import OPENAI_API_KEY


def split_mp4(input_file, output_dir, target_size_mb=25):
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # Get input file duration
    probe = ffmpeg.probe(input_file)
    duration = float(probe["format"]["duration"])

    # Calculate total file size in bytes
    total_file_size_bytes = os.path.getsize(input_file)

    # Calculate number of segments required to get close to target size
    target_size_bytes = target_size_mb * 1024 * 1024
    num_segments = math.ceil(total_file_size_bytes / target_size_bytes)

    # Calculate segment duration
    segment_duration = duration / num_segments

    # Split the input file into segments
    for i in range(num_segments):
        start_time = i * segment_duration
        end_time = min((i + 1) * segment_duration, duration)
        output_file = os.path.join(output_dir, f"{i+1}.mp4")
        ffmpeg.input(input_file, ss=start_time, to=end_time).output(
            output_file, f="mp4", vcodec="copy", acodec="copy"
        ).run(overwrite_output=True)


def mp4_to_transcription(
    mp4_filepath: str, max_size_mb: int = 25, bitrate_k: int = 64
) -> str:
    logger.info(f"Converting {mp4_filepath} to transcription")

    part_files = []

    split_mp4_folder = BASE_DIR / ".mp4"
    shutil.rmtree(split_mp4_folder, ignore_errors=True)
    split_mp4(mp4_filepath, split_mp4_folder)
    sub_indexes = [i.split(".")[0] for i in os.listdir(split_mp4_folder)]
    sub_indexes.sort()

    for i in sub_indexes:
        output_filepath = os.path.join(split_mp4_folder, f"{i}.mp4")
        logger.debug(f"ffmpeg processing {output_filepath} to transcription")
        part_files.append(output_filepath)

    # Call OpenAI API to identify it.
    client = OpenAI(api_key=OPENAI_API_KEY)
    transcription = ""
    for output_file in part_files:
        logger.debug(f"AI processing {output_file}")
        transcription += client.audio.transcriptions.create(
            model="whisper-1", file=open(output_file, "rb"), response_format="text"
        )

    # Clean part files
    for output_file in part_files:
        os.remove(output_file)

    return transcription


def conclude_with_transcription(transcription: str) -> str:
    client = OpenAI(api_key=OPENAI_API_KEY)

    with open(os.path.join(BASE_DIR, "ytbadvisor", "prompts.yaml"), "r") as fp:
        prompts = safe_load(fp)["zh-CN"]

    response = client.chat.completions.create(
        model="gpt-4-turbo-preview",
        messages=[
            {"role": "system", "content": prompts["draw_conclusion"]},
            {"role": "user", "content": transcription},
        ],
    )
    return response.choices[0].message.content
