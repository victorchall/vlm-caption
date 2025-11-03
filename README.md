# VLM Image Captioning Tool
<p align="center">
  <img src="doc/main_gui.png" alt="VLM-Caption Main GUI" width="600">
</p>

This app uses Vision Language Models (VLM) to generate detailed captions for images through multi-turn conversations, using a separately hosted VLM models via an "OpenAI-compatible" API (*including locally hosted models*).

This is currently "beta" and features may change.

A common use case would be to automate captioning large numbers of images for later text-to-image diffusion model training or classification tasks.

Slightly old video, app overview with install: [VLM Caption, multi-turn, data-driven image captioning](https://www.youtube.com/watch?v=WZ6zK7Tc0zs)

## Table of Contents

[API Service Setup](#API_Service_Setup) (for local LLM users)

[API Key use](API_KEY.MD) (for cloud API users)

[Install VLM Caption](Install)

[Features](Features)

[Hint Sources](Hint_Sources)

[Tips](Tips)

[Dev/Contribution](DEV.MD)

## Install

- Visit https://github.com/victorchall/vlm-caption/releases click on `Assets` to expand the the download links.  You have two options to use the application.

    a. The cli (command line) app is just a zip file with  `caption.yaml`  and `caption_openai.exe`.  Unzip whereever you like. 
    - Edit the `caption.yaml` with the text editor of your choice then run the `caption_openai.exe`.

    Delete it to uninstall. To update, you can delete the old version or unzip it to the same location and overwrite. 
    
    b. The electron version is a GUI app delivered as a one-click installer that will give you a GUI to edit configurations instead of manually editing the caption.yaml file.  It will install and add a shortcut to your desktop.

    *You will need to Enable CORS on your VLM service. This is a simple toggle in LM Studio.*

    Uninstall via `Add or Remove programs` in Windows.  To update, just download a newer version and install again, it will overwrite the old version.


## Features

- **Multi-turn Conversations**: Configure a series of prompts to guide the VLM through detailed image analysis
- **Multiple API Support**: Compatible with most common local/offline LLM servers, OpenAI, Anthropic, Google Gemini, etc.
- **Global Metadata**: Optionally include character databases, location reference, or other material in system prompts
- **Hint Sources**: Optionally include additional per-image or per-directory metadata (file paths, folder metadata.json, {imagename}.json) in prompts on a per-image basis, with easy developer extension
- **Bulk Processing**: Process entire directories of images
- **Output**: Saves captions as .txt files alongside original images

The GUI is a simple wrapper to edit `caption.yaml` if you wish to just use CLI.

## Configuration

All settings are configured through `caption.yaml` when using the CLI version.  The GUI version has the same config, just presented in GUI form for ease.

**The Configuration file MUST be modified for your project and system.**

### API Configuration

Most of this is covered in [API Service Setup](API_Service_Setup) for local users.

### CLI 
If you just want to use the CLI, the entire app is driven by `caption.yaml`. Edit then run the CLI by running `python caption_openai.py`.  
```yaml
# API endpoint - can be local LLM server or cloud service
base_url: "http://localhost:1234/v1"
# base_url: "https://api.openai.com/v1"

# API key handling
api_key: ""  # Leave empty for local servers
# api_key: "OPENAI_API_KEY"  # Use env var name for cloud APIs

# Model selection
model: "gemma-3-27b-it"
# model: "gpt-4o-mini"
# model: "claude-sonnet-4-20250514"

max_tokens: 16384
```

**System Prompt**: Base instructions for the VLM.  Think of this as a global instruction that you likely will not modify per project.
```yaml
system_prompt: "You are to analyze an image and provide information based on what is visible in the image. Do not embellish, preferring to focus on factual information."
```

**Global Metadata**: Optional file to include additional context (e.g., character databases)
```yaml
global_metadata_file: "character_info.txt"
```

This is a great way to add a large text file with descriptions of all the locations, characters, and objects that might appear in any of the images to help the VLM identify things by their proper names instead of generic pronouns.

If you don't have this information, set it to empty quotes `""` like this or leave it empty on the GUI:

```yaml
global_metadata_file: ""
```

See the example provided, `character_info.txt`, that includes detailed descriptions about the Final Fantasy VII Rebirth universe.  Keep in mind that very large documents will increase VRAM usage, but this is also a very useful feature to help aid the VLM identifying things like specific characters and locations by their proper names.  Otherwise, VLMs may not recognize specific things in the image unless they are very common on the internet.  I.e. A good VLM model will probably recognize Mario or Cloud Strife, but not some side character that is less popular.


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

### Tips

- The **final prompt's response** becomes the saved caption. I strongly recommend asking for a summary similar to the above example. 

- The more prompts you include the more VRAM and context will be required. 

- Check your service documentation for configuration to make sure the context window is sufficient.

- The above example is very strong when used with a more powerful VLM (like Gemma3 27B) and a large global metadata file with detailed descriptions.

- Experiment with small amounts of data to tweak your prompts.

### Hint Sources

Enable additional context sources that get prepended to the first prompt. 

```yaml
hint_sources:
  - full_path  # Includes file path information
  - json # tries to read a .json file of the same basename for each image
  - metadata # tries to read a metadata.json in the same folder as each image
```

If a source isn't available for a given image, it is skipped.  For instances if you use `json` above and an image named `cloud_strife.jpeg` has no `cloud_strife.json` in the same directory, the hint is skipped.

See [HINTSOURCES.md](HINTSOURCES.md) for details on available hint sources and how they work. 

[Developers](DEV.MD) can also add their own custom hint sources.

### Directory Processing

```yaml
base_directory: "C:/path/to/images"  # Root directory to process
# base_directory: "/mnt/path/to/images"  # POSIX style path
recursive: false  # Enable recursive subdirectory processing
```
Mostly self explanatory.  Paste in the path to the directory you want processed and set the recursive to `true` to walk all subdirectories.

## Tips

- **Prompt Tuning**: Read [PROMPTS.MD](PROMPTS.MD) for more tips on tuning your system prompt and prompt series.

- **Presort Data**: Sort your data into subdirectories ahead of time with directory names that might help steer the model, such as `c:/myimages/cloud strife` and `c:/myimages/rufus shinra/`, then use the `full_path` hint_source. 

- **Utilize metadata**: Try writing a text file with details of the overall "universe" of your image data and reference the txt file with `global_metadata_file` in `caption.yaml`. Use the example `global_metadata_file: "character_info.txt"` as a reference for what to do.

- **Model Selection**: Different models may excel at different types of image analysis. 
    
    If you have a >=24GB GPU, I highly recommend Gemma 27B (`gemma-3-27b-it`).  Q4_K_M is about 19.5GB, leaving ~4GB for context and kv caching which is typically sufficient. If you have 32GB or more, use a larger quantization (Q5_K_M, Q8_0, etc). 

    InternVL3-14B is a good alternative smaller model for users with 16GB or less. 

    Models published by `unsloth` or `lmstudio-community` are generally reliable and will work.  Sometimes some models are not properly marked as vision capable or are misconfigured.  If it doesn't seem to work, see if there is an unsloth or lmstudio-community verson.

    Not all models are suitable for multi-turn conversation. Try different models, or you can try a single prompt.

    Test the model directly in the Chat window in LM Studio to see how it responds and to workshop your series of prompts.  Or try running VLM Caption on a directory with just a few images, then check the .txt outputs. 

- **Cuda OOM or Failures**: You may need to reduce the number of prompts in your chain if you run out of VRAM, or select a smaller quantization of the model (Q3_K_S, etc), or select a smaller model. You may also need to configure your service to increase the context size as the default is often 4096, which you could exceed with very long chains of prompts, a very large metadata sources, leading to unintended outputs depending on how your service truncates context. Refer to the documentation of your service for more information.

## Advanced tip

- **Metadata collection**: Adding context is **incredibly powerful**. *Think ahead* when you decide to collect and build a new dataset considering how you can capture other metadata. 

    For instance, if you are writing webscrapers, make sure to collect metadata from the webpage as you go rather than blindly just download each image. Perhaps you might include the website address or full URI of the webpage, the `<title>` tag from the webpage, or the `alt-text` field. Save this information with each image, or in a database. Then feed into the VLM with a `hint_source`. New hint sources are very easy for an amateur Python programmer to write, or you can have an LLM write for you. 

    See [HINTSOURCES.md](HINTSOURCES.md) for more information.

- **Batch concurrency**: If you use a VLM host that support batch concurrency such as llama.cpp (via -np n arg) you can potentially increase speed. This is not supported by LM Studio.  Example command: `llama-server -np 4 -c 32768 --mmproj "mmproj-Qwen3-VL-32B-Instruct-F16.gguf" --model "Qwen3-VL-32B-Instruct-Q4_K_M.gguf" -dev cuda0 --top-k 30 --top-p 0.95 --min-p 0.05 --temp 0.5` would launch Qwen3VL 32B with four concurrent processes (-np 4) each with 8192 tokens (32768/4) of context for each of the 4 slots.  This requires additional processing power and an increase of total context size (`-np 4 -c 32768` instead of `-np 1 -c 8192` as an example), but may increase total token generation speeds by utilizing batch processing.  _This feature does not utilize the OpenAI jsonl batch API suitable for commercial APIs to save on costs, but should work to speed up rates._
