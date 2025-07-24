import base64
from PIL import Image
import asyncio
import openai
import json
import aiofiles
from omegaconf import OmegaConf
import os
from file_utils.file_access import image_walk, save_caption
from hints.hint_sources import get_hints
import logging
from typing import Tuple, Dict, List

def remove_base64_image(messages: List) -> List:
    """ Removes the base64 image from a messages for the sake of logging """
    for message in messages:
        for content_item in message.get("content", []):
            if (isinstance(content_item, dict)
                and content_item.get("type") == "image_url"
                and isinstance(content_item.get("image_url"), dict)):
                    content_item["image_url"]["url"] = "...removed..."
    return messages

def resolve_api_key(config):
    api_key_value = config.api_key.strip()

    if not api_key_value:
        return ""

    allowed_env_vars = config.get('api_key_env_vars', [])

    if api_key_value in allowed_env_vars:
        env_var_value = os.getenv(api_key_value)
        if not env_var_value:
            raise ValueError(f"Required environment variable '{api_key_value}' is not set, check that you have set the env var value, or check your config file api_key")
        return env_var_value  # Case 3: Read from env var

    return api_key_value

async def write_debug_messages(messages: List, i: int):
    async with aiofiles.open(f"messages_{i}.txt", "w") as f:
        await f.write(json.dumps(messages,indent=2))

async def process_image(client: openai.AsyncOpenAI, image_path, conf) -> Tuple[str,str,int,int]:
    """Process a single image and generate caption using an OpenAI compatible API. 
    returns a tuple of: [final response, chat history jsondumps, prompt_tokens_usage, completion_tokens_usage]"""
    # Convert image to base64 string
    async with aiofiles.open(image_path, "rb") as image_file:
        file_contents = await image_file.read()
        b64_image = base64.b64encode(file_contents).decode("utf-8")

    messages = []
    prompts = conf.prompts
    completion_tokens_usage = 0
    prompt_tokens_usage = 0

    if conf.get("system_prompt"):
        messages.append({"role": "system", "content": conf.system_prompt})
    
    hints = get_hints(conf.get("hint_sources", []), image_path)

    first_prompt_text = prompts[0]
    if hints:
        first_prompt_text = f"{hints}\n\n{prompts[0]}"
        
    first_message = [{"type": "text", "text": first_prompt_text},
                     {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64_image}"}}]
    messages.append({"role": "user", "content": first_message})

    stream = await client.chat.completions.create(
        model=conf.model,
        messages=messages,
        stream=True,
        max_tokens=conf.max_tokens,
    )

    response_text = ""
    async for event in stream:
        if event.choices and event.choices[0].delta.content is not None:
            chunk = event.choices[0].delta.content
            #print(chunk, end="")
            response_text += chunk  # Accumulate the response text

    messages.append({"role": "assistant", "content": [{"type": "text", "text": response_text}]})
    i=0
    save_debug_task = asyncio.create_task(write_debug_messages(messages, i))

    if len(prompts) > 1:
        for prompt in prompts[1:]:
            response_text = ""
            #print(f"\n ----> REQUESTING: {prompt}")
            messages.append({"role": "user", "content": [{"type": "text", "text": prompt}]})

            stream = await client.chat.completions.create(
                    model=conf.model,
                    messages=messages,
                    stream=True,
                    stream_options={"include_usage": True}
                    )
            await save_debug_task

            async for event in stream:
                if event.choices and event.choices[0].delta.content is not None:
                    chunk = event.choices[0].delta.content
                    #print(chunk, end="")
                    response_text += chunk  # Accumulate the response text
                if event.usage:
                    completion_tokens_usage += event.usage.completion_tokens
                    prompt_tokens_usage += event.usage.prompt_tokens
            messages.append({"role": "assistant", "content": [{"type": "text", "text": response_text}]})
            save_debug_task = asyncio.create_task(write_debug_messages(messages, i))
            i += 1
    await save_debug_task
    response_text = response_text.strip()
    messages = remove_base64_image(messages)
    return response_text, json.dumps(messages, indent=2), prompt_tokens_usage, completion_tokens_usage

async def main():
    import hints.registration as registration
    registration._validate_hint_sources()

    conf = OmegaConf.load("caption.yaml")

    if conf.get("global_metadata_file"): # type: ignore
        async with aiofiles.open(conf.global_metadata_file) as f:
            global_metadata = await f.read()
            conf.system_prompt = f"{global_metadata}\n{conf.system_prompt}"

    print(f" -> SYSTEM PROMPT:\n{conf.system_prompt}\n")

    api_key = resolve_api_key(conf)

    client = openai.AsyncOpenAI(base_url=conf.base_url, api_key=api_key)

    aggregated_prompt_token_usage = 0
    aggregated_completion_token_usage = 0

    async for image_path in image_walk(conf.base_directory, recursive=conf.recursive, skip_if_txt_exists=conf.skip_if_txt_exists):
        current_task = asyncio.current_task()
        if current_task is not None and current_task.cancelled():
            print("Captioning task was cancelled by user")
            return

        print(f"\nProcessing {image_path}")
        try:
            caption_text, chat_history, prompt_token_usage, completion_token_usage = await process_image(client, image_path, conf)
        except openai.APIConnectionError as e:
            print(f"{e}\nAPI Error. Check that your service is running and caption.yaml has the correct base_url")
        except asyncio.CancelledError:
            print("Captioning task was cancelled during image processing")
            raise

        # aggregated_prompt_token_usage += prompt_token_usage
        # aggregated_completion_token_usage += aggregated_completion_token_usage

        print(f" --> Final caption:\n{caption_text}")
        print(f" --> prompt_token_usage: {prompt_token_usage}, completion_token_usage: {completion_token_usage}")
        await save_caption(file_path=image_path, caption_text=caption_text, debug_info=chat_history)

    print(F" -> JOB COMPLETE.")
    # not working?
    print(f"aggregated_prompt_token_usage: {aggregated_prompt_token_usage}, aggregated_completion_token_usage: {aggregated_completion_token_usage}")

if __name__ == "__main__":
    asyncio.run(main())
