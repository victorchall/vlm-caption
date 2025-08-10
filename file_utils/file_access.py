import os
import aiofiles
from typing import AsyncGenerator
import asyncio
from ..caption_openai import filter_ascii

# Supported image extensions
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp')

async def image_walk(base_directory: str, recursive: bool, skip_if_txt_exists: bool) -> AsyncGenerator[str, None]:
    """
    Asynchronously walk through the directory and yield image file paths.

    Args:
        base_directory (str): The root directory to start searching from
        recursive (bool): Whether to search recursively

    Yields:
        str: Path to each image file found
    """
    try:
        entries = os.listdir(base_directory) # TODO: this is still blocking...

        for entry in entries:
            current_path = os.path.join(base_directory, entry)

            if recursive and os.path.isdir(current_path):
                async for image_path in image_walk(base_directory=current_path, recursive=True, skip_if_txt_exists=skip_if_txt_exists):
                    yield image_path
            elif not recursive and os.path.isdir(current_path):
                continue  # Skip directories when not recursive
            elif os.path.isfile(current_path) and current_path.lower().endswith(IMAGE_EXTENSIONS):
                if skip_if_txt_exists and os.path.exists(f"{os.path.splitext(current_path)[0]}.txt"):
                        continue
                yield current_path

    except Exception as e:
        print(f"Error accessing directory {base_directory}: {e}")

async def save_caption(file_path: str, caption_text: str, debug_info: str) -> None:
    """
    Save the caption text to a .txt and debug_info to a .log file with the same basename in the same directory as file_path.

    Args:
        file_path (str): The path to the image file
        caption_text (str): The caption text to save
        debug_info (str): Logging info

    Returns:
        None
    """
    try:
        dir_name = os.path.dirname(file_path)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        txt_path = os.path.join(dir_name, f"{base_name}.txt")
        #debug_path = os.path.join(dir_name, f"{base_name}.log")

        # Write caption text to the file
        async with aiofiles.open(txt_path, "w", encoding="utf-8") as f_cap:
                #aiofiles.open(debug_path, "w", encoding="utf-8") as f_log:
            #await asyncio.gather(f_cap.write(caption_text),f_log.write(debug_info))
            await asyncio.gather(f_cap.write(caption_text))

        print(filter_ascii(f" ----> Saved caption for {file_path} to {txt_path}"))

    except Exception as e:
        print(f"Error saving caption for {file_path}: {e}")
