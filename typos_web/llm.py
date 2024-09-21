import os
from typing import Generator

import anthropic
import openai


anthropic_client = anthropic.Client(api_key=os.getenv("ANTHROPIC_API_KEY"))


def ai_stream(
    system: str,
    messages: list[dict[str, str]],
    model: str,
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
    else:
        response = openai.chat.completions.create(
            model=model,
            messages=[
                dict(role="system", content=system),
                *messages,
            ],  # type: ignore
            stream=True,
            **kwargs,
        )

        for chunk in response:
            text = chunk.choices[0].delta.content
            if text is None:
                break
            yield text
