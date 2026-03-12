import re
from typing import List

def filter_thinking(text: str) -> str:
    """
    Removes thinking/reasoning blocks from model output.
    Handles cases where <think> may be missing but </think> is present
    (e.g. vLLM stripping the opening tag), as well as complete <think>...</think> blocks.
    """
    # Remove complete <think>...</think> blocks (with optional whitespace variants)
    text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
    # Handle missing opening <think>: remove everything before </think> if no <think> precedes it
    if '</think>' in text and '<think>' not in text:
        text = text.split('</think>', 1)[1]
    return text.strip()

def filter_caption(caption: str) -> str:
    """
    Removes a mistake in GLM 4.6V that leads to erroneous bbox related tokens
    being added to output despite not asking for grounding/location.
    """
    caption = caption.replace("<|begin_of_box|>", "")
    caption = caption.replace("<|end_of_box|>", "")
    return caption

def filter_ascii(input_str):
    """
    Removes any characters outside the standard 7-bit ASCII range (0–127).
    Currently to deal with issues when std out is streamed to GUI.
    """
    return ''.join(
        ch if ord(ch) <= 126 else "?"
        for ch in input_str
    )

def remove_base64_image(messages: List) -> List:
    """ Removes the base64 image from a messages for the sake of logging """
    for message in messages:
        for content_item in message.get("content", []):
            if (isinstance(content_item, dict)
                and content_item.get("type") == "image_url"
                and isinstance(content_item.get("image_url"), dict)):
                    content_item["image_url"]["url"] = "...removed..."
    return messages
