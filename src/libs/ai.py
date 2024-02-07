import os

from loguru import logger
from openai import OpenAI
from pydub import AudioSegment
from yaml import safe_load

from alpacurf.settings import BASE_DIR
from alpacurf.settings import OPENAI_API_KEY


def mp4_to_transcription(
    mp4_filepath: str, max_size_mb: int = 25, bitrate_k: int = 64
) -> str:
    logger.info(f"Converting {mp4_filepath} with bitrate of {bitrate_k}K")

    # Load the MP4 file
    audio = AudioSegment.from_file(mp4_filepath)

    # Calculate the maximum size of each split part in bytes
    max_size_bytes = max_size_mb * 1024 * 1024

    # Initialize variables
    start = 0
    file_index = 1
    part_files = []

    while start < len(audio):
        # Calculate the end position for the current segment
        end = start + max_size_bytes

        # Check if end is beyond audio length
        if end > len(audio):
            end = len(audio)

        # Extract segment
        segment = audio[start:end]

        # Export segment to output file
        output_file = f"part_{file_index}.mp4"
        temp_output_file = f"temp_{output_file}"
        segment.export(temp_output_file, format="mp4")

        # Check the size of the exported file
        output_file_size = os.path.getsize(temp_output_file)
        logger.debug(
            f"File {output_file} size {int(output_file_size / 1024 / 1024)} MB"
        )

        # Adjust segment size if needed
        while output_file_size > max_size_bytes:
            # Decrease segment size
            segment = segment[:-60000]  # Remove 60000 ms (60 second) from the end
            # Export the adjusted segment to the output file
            segment.export(temp_output_file, format="mp4", bitrate=f"{bitrate_k}k")
            # Update the size of the exported file
            output_file_size = os.path.getsize(temp_output_file)

            logger.debug(
                f"File {output_file} size {int(output_file_size / 1024 / 1024)} MB"
            )

        # Rename temp file to final file name
        os.rename(temp_output_file, output_file)

        # Add the output file to the list of part files
        part_files.append(output_file)

        # Update start position for the next segment
        start = end

        # Increment file index
        file_index += 1

    # Call OpenAI API to identify it.
    logger.debug("Calling OpenAI API to transcribe")

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
