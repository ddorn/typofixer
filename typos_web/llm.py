import os
from typing import Callable, Generator

import anthropic
import openai


anthropic_client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))


def ai_stream(
    system: str,
    messages: list[dict[str, str]],
    model: str,
    usage_callback: Callable[[int, int], None] = lambda x, y: None,
    **kwargs,
) -> Generator[str, None, None]:
    """Stream with the AI using the given messages."""

    new_kwargs = dict(
        max_tokens=1000,
        temperature=0.2,
    )
    kwargs = {**new_kwargs, **kwargs}

    if "claude" in model:

        if messages[-1]["role"] == "assistant":
            yield messages[-1]["content"]

        with anthropic_client.messages.stream(
            model=model,
            messages=messages,
            system=system,
            **kwargs,
        ) as stream:
            for text in stream.text_stream:
                yield text

            usage = stream.get_final_message().usage
            usage_callback(usage.input_tokens, usage.output_tokens)
    else:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                dict(role="system", content=system),
                *messages,
            ],  # type: ignore
            stream=True,
            stream_options=dict(include_usage=True),
            **kwargs,
        )

        for chunk in response:
            if not chunk.choices:
                # This is the last chunk, with the usage
                usage_callback(chunk.usage.prompt_tokens, chunk.usage.completion_tokens)
                print("Usage", chunk.usage)
            else:
                text = chunk.choices[0].delta.content
                if text is not None:
                    yield text
