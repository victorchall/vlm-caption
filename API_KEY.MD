
## API Key Security

Generally, locally hosted LLMs need no API key. `api_key: ""` or leave the API Key field in the GUI blank.  

### If you are using a locally hosted LLM with no API key you can ignore the rest of this document.

For cloud APIs, I recommend using environment variables for your api keys, but API key security is your responsibility!

1. Set environment variable: 

    a. For Windows, set environment variable permanently in the Windows `Environment Variables` for either GUI or CLI. You may need to reboot for this to take effect. ![alt text](doc/env_var_win.png)

    b. For POSIX systems, `export OPENAI_API_KEY=your_key_here`. I will assume Linux users know what they're doing to configure an env var in shell startup scripts.

2. Use "OPENAI_API_KEY" as your API Key in VLM Caption:

    a. For CLI users, Reference your env var in `config.yaml`: `api_key: "OPENAI_API_KEY"` 

    b. For GUI users, paste `OPENAI_API_KEY` into the GUI's API Key field. 

## Literal API key value

Using an environment variable (above) is generally preferred.

The value of `api_key` will be used literally if it is not a value listed here:
- OPENAI_API_KEY
- ANTHROPIC_API_KEY
- GEMINI_API_KEY
- MY_API_KEY_ENV_VAR_NAME

If you have a different env var name, like MYAWESOMECLOUD_API_KEY you can add it to `caption.yaml` as an env var reference under the `api_key_env_vars` key. This causes the application to read the env var instead of using the api key as a literal.

### Use:

1. For CLI users, in `caption.yaml` paste your api key ito the `api_key` field. 

ex. `api_key: "asdfqwerty1234567890foobarbazqux"` 

2. For GUI users, paste your actual API key into the GUI
