import os
import json
import aiofiles
from typing import AsyncGenerator, List, Optional
import asyncio

# Supported image extensions
IMAGE_EXTENSIONS = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp', '.avif')

OUTPUT_FORMAT_TXT = "txt"
OUTPUT_FORMAT_JSONL = "jsonl"


def concat_prompts(prompts: List[str]) -> str:
    """Join the per-turn prompts into a single identity string used for jsonl matching."""
    if not prompts:
        return ""
    return "\n\n".join(prompts)


def _txt_path_for(image_path: str) -> str:
    return f"{os.path.splitext(image_path)[0]}.txt"


def _jsonl_path_for(image_path: str) -> str:
    return f"{os.path.splitext(image_path)[0]}.jsonl"


def caption_exists(image_path: str, output_format: str, model: str = "", concat_prompt: str = "") -> bool:
    """Return True if a caption already exists for this image under the given format.

    For txt format: a sidecar .txt file next to the image.
    For jsonl format: any line in the sidecar .jsonl whose model and prompt match.
    """
    if output_format == OUTPUT_FORMAT_JSONL:
        jsonl_path = _jsonl_path_for(image_path)
        if not os.path.exists(jsonl_path):
            return False
        try:
            with open(jsonl_path, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        entry = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if entry.get("model") == model and entry.get("prompt") == concat_prompt:
                        return True
        except Exception as e:
            print(f"Error reading {jsonl_path}: {e}")
        return False

    # default: txt
    return os.path.exists(_txt_path_for(image_path))


async def image_walk(
    base_directory: str,
    recursive: bool,
    skip_if_caption_exists: bool,
    output_format: str = OUTPUT_FORMAT_TXT,
    model: str = "",
    concat_prompt: str = "",
) -> AsyncGenerator[str, None]:
    """
    Asynchronously walk through the directory and yield image file paths.

    When skip_if_caption_exists is True, images that already have a matching
    caption (per output_format / model / concat_prompt) are skipped.
    """
    try:
        entries = os.listdir(base_directory)  # TODO: this is still blocking...

        for entry in entries:
            current_path = os.path.join(base_directory, entry)

            if recursive and os.path.isdir(current_path):
                async for image_path in image_walk(
                    base_directory=current_path,
                    recursive=True,
                    skip_if_caption_exists=skip_if_caption_exists,
                    output_format=output_format,
                    model=model,
                    concat_prompt=concat_prompt,
                ):
                    yield image_path
            elif not recursive and os.path.isdir(current_path):
                continue
            elif os.path.isfile(current_path) and current_path.lower().endswith(IMAGE_EXTENSIONS):
                if skip_if_caption_exists and caption_exists(
                    current_path, output_format, model=model, concat_prompt=concat_prompt
                ):
                    continue
                yield current_path

    except Exception as e:
        print(f"Error accessing directory {base_directory}: {e}")


async def save_caption(
    file_path: str,
    caption_text: str,
    debug_info: str,
    output_format: str = OUTPUT_FORMAT_TXT,
    model: str = "",
    concat_prompt: str = "",
) -> None:
    """
    Save the caption for the given image.

    txt: write/overwrite a .txt sidecar with caption_text.
    jsonl: append one JSON object per line ({"text", "model", "prompt"}) so multiple
    captions per image (different models/prompt sets) can coexist.
    """
    try:
        if output_format == OUTPUT_FORMAT_JSONL:
            jsonl_path = _jsonl_path_for(file_path)
            entry = {"text": caption_text, "model": model, "prompt": concat_prompt}
            line = json.dumps(entry, ensure_ascii=False) + "\n"
            async with aiofiles.open(jsonl_path, "a", encoding="utf-8") as f_cap:
                await f_cap.write(line)
            return

        txt_path = _txt_path_for(file_path)
        async with aiofiles.open(txt_path, "w", encoding="utf-8") as f_cap:
            await asyncio.gather(f_cap.write(caption_text))

    except Exception as e:
        print(f"Error saving caption for {file_path}: {e}")
