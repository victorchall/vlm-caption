import openai
from typing import List, Tuple

async def run_summary_retry_rules(client:openai.AsyncClient, 
                                  conf, 
                                  messages:List, 
                                  summary_response:str, 
                                  completion_tokens_usage,
                                  prompt_tokens_usage) -> Tuple[str, int, int]:
    def run_rules(retry_rules, response_to_check) -> dict:
        rejections = {}
        for rule in retry_rules:
            rule_name = rule.get("rule_name", None)
            rejection_note = rule.get("rejection_note", None)
            if not rejection_note:
                continue
            rejection_phrases = rule.get("phrases", [])
            found_rejected_phrases = []
            for phrase in rejection_phrases:
                if phrase in response_to_check:
                    found_rejected_phrases.append(phrase)
            if len(found_rejected_phrases) > 0:
                rejections[rejection_note] = found_rejected_phrases
        return rejections

    retry_rules = conf.get("retry_rules", [])
    if len(retry_rules) < 1:
        return summary_response, completion_tokens_usage, prompt_tokens_usage 

    rejections = run_rules(retry_rules, summary_response)

    if len(rejections.keys()) == 0:
        return summary_response, completion_tokens_usage, prompt_tokens_usage

    print("  --> Found rejected phrase, retrying summary")
    retry_request_message = ""
    for rejection_note in rejections.keys():
        retry_request_message += rejection_note.replace("[phrases]", ", ".join(rejections[rejection_note])) + "\n"
    retry_request_message.strip() # remove final line break

    messages.append({"role": "user", "content": [{"type": "text", "text": retry_request_message}]})
    stream = await client.chat.completions.create(
        model=conf["model"],
        messages=messages,
        stream=True,
        stream_options={"include_usage": True}
        )

    response_text = ""
    async for event in stream:
        if event.choices and event.choices[0].delta.content is not None:
            chunk = event.choices[0].delta.content
            response_text += chunk
        if event.usage:
            completion_tokens_usage += event.usage.completion_tokens
            prompt_tokens_usage += event.usage.prompt_tokens

    rejections = run_rules(retry_rules, response_text)

    if len(rejections.keys()) > 0:
        print("     --> Failed to fix rejected phrase(s), returning original response")
        return summary_response, completion_tokens_usage, prompt_tokens_usage
    else:
        print("     --> Rejected phrases corrected.")

    return response_text, completion_tokens_usage, prompt_tokens_usage
