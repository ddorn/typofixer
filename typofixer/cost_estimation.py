from dataclasses import dataclass

import constants


@dataclass
class CostEstimation:
    input_tokens: int
    input_cost: float
    output_cost: float
    is_approximate: bool

    def __str__(self):
        return (
            f"Cost for {self.input_tokens} tokens: "
            f"{self.input_cost:.4f}$ + "
            f"{self.output_cost * 1000:.4f}$/1k output tokens"
        )

    @classmethod
    def estimate(cls, messages: list[dict], model: str) -> "CostEstimation":
        """Estimate the cost of the AI completion."""

        import tiktoken

        input_cost, output_cost = constants.MODELS_COSTS[model]

        try:
            encoding = tiktoken.encoding_for_model(model)
            approx = False
        except KeyError:
            # This makes it work also for Anthropic models.
            # This will be less accurate than for OpenAI, but their tokenization is not public
            encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")
            approx = True

        input_tokens = 0
        for msg in messages:
            input_tokens += len(encoding.encode(msg["content"]))
            input_tokens += 4  # for the role and the separator

        return cls(
            input_tokens=input_tokens,
            input_cost=input_cost * input_tokens / 1_000_000,
            output_cost=output_cost / 1_000_000,
            is_approximate=approx,
        )
