import base64
from PIL import Image
import asyncio
import openai
import json
import aiofiles
import time
from omegaconf import OmegaConf
import os
from file_utils.file_access import image_walk, save_caption
from hints.hint_sources import get_hints
import logging
from typing import Tuple, Dict, List
from rules.summary_retry import run_summary_retry_rules


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
        if event.usage:
            completion_tokens_usage += event.usage.completion_tokens
            prompt_tokens_usage += event.usage.prompt_tokens

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
                    response_text += chunk
                if event.usage:
                    completion_tokens_usage += event.usage.completion_tokens
                    prompt_tokens_usage += event.usage.prompt_tokens
            messages.append({"role": "assistant", "content": [{"type": "text", "text": response_text}]})
            save_debug_task = asyncio.create_task(write_debug_messages(messages, i))
            i += 1
            final_summary_response = response_text
            if i == len(prompts)-1:
                final_summary_response, completion_tokens_usage, prompt_tokens_usage = await \
                    run_summary_retry_rules(client, 
                                            conf, 
                                            messages, 
                                            summary_response=response_text,
                                            completion_tokens_usage=completion_tokens_usage,
                                            prompt_tokens_usage=completion_tokens_usage)
    else:
        final_summary_response = response_text

    await save_debug_task
    final_summary_response = final_summary_response.strip()
    messages = remove_base64_image(messages)
    return final_summary_response, json.dumps(messages, indent=2), prompt_tokens_usage, completion_tokens_usage

async def process_batch(client: openai.AsyncOpenAI, image_paths: list, conf) -> Tuple[int, int]:
    """Process a batch of images concurrently and return aggregated token usage."""
    tasks = [process_image(client, image_path, conf) for image_path in image_paths]
    
    # Process all images in the batch concurrently
    results = await asyncio.gather(*tasks, return_exceptions=True)

    batch_prompt_tokens = 0
    batch_completion_tokens = 0

    for i, result in enumerate(results):
        if isinstance(result, Exception):
            print(filter_ascii(f"Error processing {image_paths[i]}: {result}"))
        else:
            caption_text, chat_history, prompt_token_usage, completion_token_usage = result # type: ignore

            await save_caption(file_path=image_paths[i], caption_text=caption_text, debug_info=chat_history)

            batch_prompt_tokens += prompt_token_usage
            batch_completion_tokens += completion_token_usage

            print(filter_ascii(f" --> Processed {image_paths[i]}"))
            print(f" --> prompt_token_usage: {prompt_token_usage}, completion_token_usage: {completion_token_usage}")

    return batch_prompt_tokens, batch_completion_tokens

async def process_image_semaphore(client: openai.AsyncOpenAI, image_path: str, conf, semaphore: asyncio.Semaphore, results_queue: asyncio.Queue):
    """Process a single image with semaphore control and put results in queue."""
    async with semaphore:
        try:
            start_time = time.perf_counter()
            caption_text, chat_history, prompt_token_usage, completion_token_usage = await process_image(client, image_path, conf)
            
            await save_caption(file_path=image_path, caption_text=caption_text, debug_info=chat_history)
            
            processing_time = time.perf_counter() - start_time
            
            await results_queue.put({
                'image_path': image_path,
                'caption_text': caption_text,
                'prompt_token_usage': prompt_token_usage,
                'completion_token_usage': completion_token_usage,
                'processing_time': processing_time,
                'success': True
            })
            
        except Exception as e:
            await results_queue.put({
                'image_path': image_path,
                'error': str(e),
                'success': False
            })

async def main():
    import hints.registration as registration
    registration._validate_hint_sources()

    conf = OmegaConf.load("caption.yaml")
    
    concurrent_batch_size = conf.concurrent_batch_size

    if conf.get("global_metadata_file"): # type: ignore
        async with aiofiles.open(conf.global_metadata_file) as f:
            global_metadata = await f.read()
            conf.system_prompt = f"{global_metadata}\n{conf.system_prompt}"

    print(filter_ascii(f" -> SYSTEM PROMPT:\n{conf.system_prompt}\n"))
    print(filter_ascii(f" -> Max concurrency: {concurrent_batch_size}\n"))

    api_key = resolve_api_key(conf)

    client = openai.AsyncOpenAI(base_url=conf.base_url, api_key=api_key)

    aggregated_prompt_token_usage = 0
    aggregated_completion_token_usage = 0
    total_images_processed = 0
    total_images_failed = 0

    semaphore = asyncio.Semaphore(concurrent_batch_size)
    results_queue = asyncio.Queue()
    active_tasks = []
    
    print(filter_ascii(f"Starting image processing...\n"))

    async for image_path in image_walk(conf.base_directory, recursive=conf.recursive, skip_if_txt_exists=conf.skip_if_txt_exists):
        current_task = asyncio.current_task()
        if current_task is not None and current_task.cancelled():
            print("Captioning task was cancelled by user")
            for task in active_tasks:
                task.cancel()
            return

        task = asyncio.create_task(process_image_semaphore(client, image_path, conf, semaphore, results_queue))
        active_tasks.append(task)

    while active_tasks:
        try:
            result = await asyncio.wait_for(results_queue.get(), timeout=0.025)
            if result['success']:
                total_images_processed += 1
                aggregated_prompt_token_usage += result['prompt_token_usage']
                aggregated_completion_token_usage += result['completion_token_usage']
                
                print(filter_ascii(f" --> Processed {result['image_path']}"))
                print(f"     Time: {result['processing_time']/concurrent_batch_size:.2f}s, Tokens: {result['prompt_token_usage']} prompt, {result['completion_token_usage']} completion")
            else:
                total_images_failed += 1
                print(filter_ascii(f" --> Error processing {result['image_path']}: {result['error']}"))
            
            results_queue.task_done()
        except asyncio.TimeoutError:
            pass

        active_tasks = [task for task in active_tasks if not task.done()]
        
        if not active_tasks:
            break

    # Process any remaining results
    while not results_queue.empty():
        result = await results_queue.get()
        if result['success']:
            total_images_processed += 1
            aggregated_prompt_token_usage += result['prompt_token_usage']
            aggregated_completion_token_usage += result['completion_token_usage']
        else:
            total_images_failed += 1
        results_queue.task_done()

    print(F" -> JOB COMPLETE.")
    print(f"Total images processed: {total_images_processed}")
    print(f"Total images failed: {total_images_failed}")
    print(f"aggregated_prompt_token_usage: {aggregated_prompt_token_usage}, aggregated_completion_token_usage: {aggregated_completion_token_usage}")

if __name__ == "__main__":
    asyncio.run(main())
