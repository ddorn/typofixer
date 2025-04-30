import os
import dotenv

dotenv.load_dotenv()

MAX_CHARS = 6000
CONFIG_PATH = os.getenv("CONFIG_PATH", "./config.yaml")

OPENAI_MODEL = "gpt-4o-2024-08-06"
ANTHROPIC_MODEL = "claude-3-opus-20240229"
ANTHROPIC_MODEL = "claude-3-sonnet-20240229"
ANTHROPIC_MODEL = "claude-2.1"
CHEAPEST_MODEL = "gpt-4o-mini"
CHEAP_BUT_GOOD = "gpt-4o-mini"
MODELS_COSTS = {
    "claude-3-5-sonnet-20240620": (3, 15),
    "gpt-4o": (5, 15),
    "gpt-4o-2024-08-06": (5, 15),
    "gpt-4o-mini": (0.15, 0.6),
    "gpt-3.5-turbo": (0.5, 1.5),
    "claude-3-opus-20240229": (15, 75),
    "claude-3-sonnet-20240229": (3, 15),
    "claude-3-haiku-20240229": (0.25, 1.25),
}
MODELS = list(MODELS_COSTS)
