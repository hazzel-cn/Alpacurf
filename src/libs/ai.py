import os

from openai import OpenAI
from pydub import AudioSegment
from yaml import safe_load

from alpacurf.settings import BASE_DIR
from alpacurf.settings import OPENAI_API_KEY


def mp4_to_transcription(
    mp4_filepath: str, max_size_mb: int = 20, bitrate: str = "64k"
) -> str:
    # Split the MP3 file
    audio = AudioSegment.from_file(mp4_filepath)
    max_size_bytes = max_size_mb * 1000 * 1000
    start = 0
    file_index = 1

    part_files = []

    while start < len(audio):
        end = start + max_size_bytes
        # Check if end is beyond audio length
        if end > len(audio):
            end = len(audio)

        # Extract segment
        segment = audio[start:end]
        # Define output file path
        output_file = f"part_{file_index}.mp3"
        part_files.append(output_file)
        # Export segment to output file
        segment.export(output_file, format="mp3", bitrate=bitrate)
        # Update start point for next segment
        start = end
        # Increment file index
        file_index += 1

    # Call OpenAI API to identify it.
    client = OpenAI(api_key=OPENAI_API_KEY)
    transcription = ""
    for output_file in part_files:
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
