
## API Service Setup

You can use a paid API like OpenAI, Anthropic, or Google Gemini by configuring your [API key](API_KEY.MD), however for local hosting, you'll need a service to host your VLM model.

1. Install one of the following: [LM Studio](https://lmstudio.ai/download), [vllm](https://github.com/vllm-project/vllm), [ollama](https://ollama.com/download), or any other local LLM service that serves via the "OpenAI API" (most of them do). 
    
    LM Studio is likely the easiest for most people to get working since it is entirely GUI based. I've only included extra steps below for LM Studio. If you want to use ollama, vllm, or another service, please refer to that application's documentation for installation. 

2. Download your preferred model inside the service you installed. You should select a model and quant that is a few gigabytes less than your VRAM to leave room for context.
    
    a. For LM Studio, open the app and go to Discover, search for models and download one. 

3. Make sure local hosting is enabled:
   
    a. For LM Studio, enable developer mode (bottom left  `User - Power User - Developer`, click on `Developer`), then go to the `Developer` section, at the top left click the toggle to enable the service. Make sure to copy the uri shown at the top right (see point 5 below).
    
    ![Toggle Service in LM Studio](doc/lm_studio_dev.png)

    If you are using the standalone GUI, you will also need to `Enable CORS` to allow app to call the LM Studio service API.
    ![Enable CORS in LM Studio](doc/enable_cors.png)


4. Make sure the service works.  You can typically check the /v1/models route in any web browser to make sure the service is running and models are available to serve. (ex. something like `http://192.168.0.5:11434/v1/models` or `http://localhost:1234/v1/models` -- just open in Chrome)

5.  Paste the IP and port and paste into `caption.yaml` in the `base_url` value, and add `/v1`.  You may also see `localhost` in place of the IP if you are not configured to host to the rest of your local network.
    ![alt text](doc/base_url.png)

Congrats! You're running your own offline LLM/VLM server. 

*Check the documentation for the server/app you are using if you need more information or support on configuring your service. Further info for LM Studio is [here](https://lmstudio.ai/docs/app/api)*