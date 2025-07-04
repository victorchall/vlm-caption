# VLM Image Captioning Tool

This app uses Vision Language Models (VLM) to generate detailed captions for images through multi-turn conversations with VLM AI models via an "OpenAI-compatible" API (*including locally hosted models*).

This is currently "beta" and features may change.

A common use case would be to automate captioning large numbers of images for later text-to-image diffusion model training or classification tasks.

## Features

- **Multi-turn Conversations**: Configure a series of prompts to guide the VLM through detailed image analysis
- **Multiple API Support**: Compatible with most common local/offline LLM servers, OpenAI, Anthropic, Google Gemini, etc.
- **Global Metadata**: Optionally include character databases, location reference, or other material in system prompts
- **Hint Sources**: Optionally include additional per-image or per-directory metadata (file paths, folder metadata.json, {imagename}.json) in prompts on a per-image basis, with easy developer extension
- **Bulk Processing**: Process entire directories of images
- **Output**: Saves captions as .txt files alongside original images

A GUI is a work-in-progress, but will not be much more than a simple wrapper to edit `caption.yaml`, thus low priority.

## Installation

- See [API Service Setup](#API_Service_Setup) to install a VLM/LLM server of your choice.  LM Studio is extremely easy to install and use to manage models.
- Visit https://github.com/victorchall/vlm-caption/actions, click on the most recent (top) workflow run, then under `Artifacts` click on `vlm-caption` to download the latest build.  Unzip it somewhere on your computer.
- Edit the `caption.yaml` then run the `caption_openai.exe`.
    - If you prefer, you can clone the repo, setup a venv or conda env, install requirements, then run with python. This is for users with some level of python/git experience only.

## Configuration

All settings are configured through `caption.yaml`.

**The `caption.yaml` file MUST be modified for your project. Open it in something like nano or Notepad++ to edit and make sure to save it!**

### API Configuration

Most of this is covered in [API Service Setup](#API_Service_Setup) for local users. If you are using a paid API, see [API_KEY.MD](API_KEY.MD) for info on setting your API.

```yaml
# API endpoint - can be local LLM server or cloud service
base_url: "http://localhost:1234/v1"
# base_url: "https://api.openai.com/v1"
# base_url: "https://api.anthropic.com/v1"

# API key handling
api_key: ""  # Leave empty for local servers
# api_key: "OPENAI_API_KEY"  # Use env var name for cloud APIs

# Model selection
model: "gemma-3-27b-it"
# model: "gpt-4o-mini"
# model: "claude-sonnet-4-20250514"

# Token limit (adjust for local VRAM constraints)
max_tokens: 16384
```
`model` is a string that tells the service what model you want to use. It should be visible in LM Studio in your models list, or with ollama use `ollama list`, or check the documentation of whatever service you are using.

**System Prompt**: Base instructions for the VLM.  Think of this as a global instruction that you likely will not modify per project.
```yaml
system_prompt: "You are to analyze an image and provide information based on what is visible in the image. Do not embellish, preferring to focus on factual information."
```

**Global Metadata**: Optional file to include additional context (e.g., character databases)
```yaml
global_metadata_file: "character_info.txt"
```

This is a great way to add a large text file with descriptions of all the locations, characters, and objects that might appear in any of the images to help the VLM identify things by their proper names instead of generic pronouns.

If you don't have this information, set it to empty quotes `""` like this:

```yaml
global_metadata_file: ""
```

See the example provided, `character_info.txt`, that includes detailed descriptions about the Final Fantasy VII Rebirth universe.  Keep in mind that very large documents will increase VRAM usage.


**Multi-turn Prompts**: Sequential questions asked to the VLM
```yaml
prompts:
  - "What character(s) do you think are present? Support your decision based on physical features."
  - "What other objects are present in the image? What is the general scene?"
  - "Describe their outfits in detail."
  - "Describe the general composition from a photographer's perspective."
  - "Can you categorize the artistic style or medium?"
  - "Summarize the description in four sentences. No markdown or special formatting."
```

### Tips:

- The **final prompt's response** becomes the saved caption. I strongly recommend asking for a summary similar to the above example. 

- The more prompts you include the more VRAM and context will be required. 

- max_tokens may also be limited to the context length setting in your service. Check your service documentation for configuration.

- The above example is very strong when used with a more powerful VLM (like Gemma3 27B) and a large global metadata file with detailed descriptions.

- Experiment with small amounts of data to tweak your prompts.

## Hint Sources

Enable additional context sources that get prepended to the first prompt. 

```yaml
hint_sources:
  - full_path  # Includes file path information
  - json # tries to read a .json file of the same basename for each image
  - metadata # tries to read a metadata.json in the same folder as each image
```

You can add `#` to the beginning of the line to comment out ones you don't want. If a source isn't available for a given image, it is skipped.  For instances if you use `json` above and an image named `cloud_strife.jpeg` has no `cloud_strife.json` in the same directory, the hint is skipped.

See [HINTSOURCES.md](HINTSOURCES.md) for details on available hint sources and how they work. 

Developers can also add their own. PRs for generally useful hint_sources are welcome.

### Directory Processing

```yaml
base_directory: "C:/path/to/images"  # Root directory to process
# base_directory: "/mnt/path/to/images"  # POSIX style path
recursive: false  # Enable recursive subdirectory processing
```
Mostly self explanatory.  Paste in the path to the directory you want processed and set the recursive to `true` to walk all subdirectories.


## API Service Setup

You can use a paid API like OpenAI, Anthropic, or Google Gemini by configuring your [api_key](API_KEY.MD), however for local hosting, you'll need a service to host your VLM model.

1. Install one of the following: [LM Studio](https://lmstudio.ai/download), [vllm](https://github.com/vllm-project/vllm), [ollama](https://ollama.com/download), or any other local LLM service that serves via the "OpenAI API" (most of them do). 
    
    LM Studio is likely the easiest for most people to get working since it is entirely GUI based. I've only included extra steps below for LM Studio. If you want to use ollama, vllm, or another service, please refer to that application's documentation for installation. 

2. Download your preferred model inside the service you installed. You should select a model and quant that is a few gigabytes less than your VRAM to leave room for context.
    
    a. For LM Studio, open the app and go to Discover, search for models and download one. 

3. Make sure local hosting is enabled:
   
    a. For LM Studio, enable developer mode (bottom left  `User - Power User - Developer`, click on `Developer`), then go to the `Developer` section, at the top left click the toggle to enable the service. Make sure to copy the uri shown at the top right (see point 5 below).
    
    ![alt text](doc/lm_studio_dev.png)


4. Make sure the service works.  You can typically check the /v1/models route in any web browser to make sure the service is running and models are available to serve. (ex. something like `http://192.168.0.5:11434/v1/models` or `http://localhost:1234/v1/models` -- just open in Chrome)

5.  Paste the IP and port and paste into `caption.yaml` in the `base_url` value, and add `/v1`.  You may also see `localhost` in place of the IP if you are not configured to host to the rest of your local network.
    ![alt text](doc/base_url.png)

Congrats! You're running your own offline LLM/VLM server. 

*Check the documentation for the server/app you are using if you need more information or support on configuring your service. Further info for LM Studio is [here](https://lmstudio.ai/docs/app/api)*

## Tips

- **Prompt Tuning**: Experiment with different prompt sequences for better results. The example prompt chain included should give you some good ideas. Note that 1 to 5 is generally sufficient, and too many may lead to worse outcomes depending on the model used, and increased VRAM usage.

- **Presort Data**: Sort your data into subdirectories ahead of time with directory names that might help steer the model, such as `c:/myimages/cloud strife` and `c:/myimages/rufus shinra/`, then use the `full_path` hint_source. 

- **Utilize metadata**: Try writing a text file with details of the overall "universe" of your image data and reference the txt file with `global_metadata_file` in `caption.yaml`. Use the example `global_metadata_file: "character_info.txt"` as a reference for what to do.

- **Model Selection**: Different models may excel at different types of image analysis. 
    
    If you have a >=24GB GPU, I highly recommend Gemma 27B (`gemma-3-27b-it`).  Q4_K_M is about 19.5GB, leaving ~4GB for context and kv caching which is typically sufficient. If you have 32GB or more, use a larger quantization (Q5_K_M, Q8_0, etc). 

    InternVL3-14B is a good alternative smaller model for users with 16GB or less. 

    Not all models are suitable for multi-turn conversation. Try different models, or you can try a single prompt.

- **Cuda OOM or Failures**: You may need to reduce the number of prompts in your chain if you run out of VRAM, or select a smaller quantization of the model (Q3_K_S, etc), or select a smaller model. You may also need to configure your service to increase the context size as the default is often 4096, which you could exceed with very long chains of prompts, leading to unintended outputs depending on how the service truncates. Check your service logs to spot errors. Refer to the documentation of the service to change the configuration.

## Advanced tip

- **Metadata collection**: Adding context is **incredibly powerful**. *Think ahead* when you decide to collect and build a new set of data considering how you can capture other metadata. 

    For instance, if you are writing webscrapers, make sure to collect metadata from the webpage as you go rather than blindly just download each image. Perhaps you might include the website address or full URI of the webpage, the `<title>` tag from the webpage, or the `alt-text` field. Save this information with each image, or in a database. Then feed into the VLM with a `hint_source`. New hint sources are very easy for an amateur Python programmer to write, or you can have an LLM write for you. 

    See [HINTSOURCES.md](HINTSOURCES.md) for more information.