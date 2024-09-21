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

The simplest way to run the app locally is using [`pipx`](https://pipxproject.github.io/pipx/).

```bash
pipx install https://github.com/ddorn/typofixer
```
Then the app can be started with `typofixer`.

Note that you need to have the `OPENAI_API_KEY` environment variable set to your OpenAI API key to
use OpenAI models, and `ANTHROPIC_API_KEY` to use the Anthropic models.

## Modify and run locally

```bash
# Install dependencies with poetry (https://python-poetry.org/)
poetry install
# Run the app
poetry run streamlit run typo_fixer/main.py
```

<!-- If you find it useful, [please contribute](https://paypal.me/diegodorn), each request costs me ~1 cent. -->