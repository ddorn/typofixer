# LLM Typo Fixer

It's simple.
1. You input a text
2. An LLM rewrites it
3. You see the differences:
    :red[red text is yours], :green[green is suggestions].
4. You click to toggle between the original and new version.
5. Copy-Paste once you're happy!

👉 Find an instance at https://typo-correct.fly.dev/.

![Typo Fixer](./images/screenshot.webp)

## Run locally

The simplest way to run the app locally is using [`uvx`](https://docs.astral.sh/uv/#scripts)

```bash
uvx git+https://github.com/ddorn/typofixer
```

Note that you need to have the `OPENAI_API_KEY` environment variable set to your OpenAI API key to
use OpenAI models, or to create a `config.yaml` file in the `typos_web` directory with the following to use any OpenAI compatible API:

```yaml
# config.yaml
api_base: ...
api_key: ...
```

I recomand [LiteLLM Proxy](https://docs.litellm.ai/docs/proxy/docker_quick_start) with a free supabase backend.

## Modify and run locally (or to set up your own instance)

```bash
uv run streamlit run typofixer/main.py
```
