# %%
from abc import ABC, abstractmethod
from collections import namedtuple
import json
import os
from pathlib import Path
import time
from typing import Iterator
import requests
import warnings
import threading

import constants

Usage = namedtuple("Usage", ["input_tokens", "output_tokens"])


def threaded(func):
    def wrapper(*args, **kwargs):
        thread = threading.Thread(target=func, args=args, kwargs=kwargs)
        thread.start()

    return wrapper


class UsageTracker(ABC):
    @abstractmethod
    def log_call(
        self, model: str, input_text: str, output_text: str, input_tokens: int, output_tokens: int
    ):
        pass

    @abstractmethod
    def get_data_since(self, since: int) -> Iterator[dict]:
        pass

    def total_usage(self, since: int) -> dict[str, Usage]:
        """Return the total usage per model since the given timestamp."""

        total_usage = {}
        for data in self.get_data_since(since):
            model = data["model"]
            input_tokens = data["input_tokens"]
            output_tokens = data["output_tokens"]

            if model not in total_usage:
                total_usage[model] = Usage(0, 0)

            total_usage[model] = Usage(
                total_usage[model].input_tokens + input_tokens,
                total_usage[model].output_tokens + output_tokens,
            )

        return total_usage

    def total_cost(self, since: int) -> float:
        """Return the total cost of the usage since the given timestamp."""

        total_cost = 0
        for model, usage in self.total_usage(since).items():
            input_cost, output_cost = constants.MODELS_COSTS.get(model, (0, 0))
            total_cost += input_cost * usage.input_tokens + output_cost * usage.output_tokens

        return total_cost / 1_000_000

    @abstractmethod
    def requests_count(self, since: int) -> int:
        """Return the number of requests since the given timestamp."""


class FileUsageTracker(UsageTracker):
    def __init__(self, log_file: str):
        self.log_file = log_file

    def log_call(
        self, model: str, input_text: str, output_text: str, input_tokens: int, output_tokens: int
    ):
        data = {
            "model": model,
            "input_length": len(input_text),
            "output_length": len(output_text),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "date_created": time.time(),
        }

        with open(self.log_file, "a") as f:
            f.write(json.dumps(data) + "\n")

    def get_data_since(self, since: int) -> Iterator[dict]:
        with open(self.log_file) as f:
            for line in f:
                data = json.loads(line)
                if data["date_created"] > since:
                    yield data

    def requests_count(self, since: int) -> int:
        return sum(1 for _ in self.get_data_since(since))


class DirectusUsageTracker(UsageTracker):
    def __init__(self, domain: str, collection: str, token: str):
        super().__init__()

        self.domain = domain
        self.collection = collection
        self.token = token

    def log_call(
        self, model: str, input_text: str, output_text: str, input_tokens: int, output_tokens: int
    ):
        url = f"{self.domain}/items/{self.collection}"

        response = requests.post(
            url,
            json={
                "model": model,
                "input_length": len(input_text),
                "output_length": len(output_text),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
            headers={"Authorization": f"Bearer {self.token}"},
        )
        response.raise_for_status()

    def timestamp_to_directus(self, timestamp: int) -> str:
        return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(timestamp))

    def get_data_since(self, since: int) -> Iterator[dict]:
        since = self.timestamp_to_directus(since)
        url = f"{self.domain}/items/{self.collection}?filter[date_created][_gt]={since}"
        response = requests.get(url, headers={"Authorization": f"Bearer {self.token}"})
        response.raise_for_status()

        return response.json()["data"]

    def total_usage(self, since: int) -> dict[str, Usage]:
        since = self.timestamp_to_directus(since)
        url = (
            f"{self.domain}/items/{self.collection}"
            f"?filter[date_created][_gt]={since}"
            f"&groupBy[]=model"
            f"&aggregate[sum]=input_tokens"
            f"&aggregate[sum]=output_tokens"
        )
        response = requests.get(url, headers={"Authorization": f"Bearer {self.token}"})
        response.raise_for_status()
        print(response.json())

        total_usage = {}
        for data in response.json()["data"]:
            model = data["model"]
            input_tokens = data["sum"]["input_tokens"]
            output_tokens = data["sum"]["output_tokens"]

            total_usage[model] = Usage(input_tokens, output_tokens)

        return total_usage

    def requests_count(self, since: int) -> int:
        since = self.timestamp_to_directus(since)
        url = f"{self.domain}/items/{self.collection}?filter[date_created][_gt]={since}&aggregate[count]=*"
        response = requests.get(url, headers={"Authorization": f"Bearer {self.token}"})
        response.raise_for_status()

        return response.json()["data"][0]["count"]

    def export_schema(self):
        url = f"{self.domain}/schema/snapshot"
        response = requests.get(url, headers={"Authorization": f"Bearer {self.token}"})
        response.raise_for_status()
        schema = response.json()["data"]

        # Clean up schema, to have only the fields/collections we need
        schema["collections"] = [
            c for c in schema["collections"] if c["collection"] == self.collection
        ]
        schema["fields"] = [f for f in schema["fields"] if f["collection"] == self.collection]
        schema["relations"] = [r for r in schema["relations"] if r["collection"] == self.collection]

        print(json.dumps(schema, indent=2))


def tracker():

    default_log_file = Path(__file__).parent.parent / "logs.jsonl"
    TYPOFIXER_LOG_FILE = os.getenv("TYPOFIXER_LOG_FILE", str(default_log_file))

    DIRECTUS_DOMAIN = os.getenv("DIRECTUS_DOMAIN")
    DIRECTUS_COLLECTION = os.getenv("DIRECTUS_COLLECTION", "typofixer_requests")
    DIRECTUS_TOKEN = os.getenv("DIRECTUS_TOKEN")
    DIRECTUS_DISABLE = os.getenv("DIRECTUS_DISABLE")

    if DIRECTUS_DISABLE:
        return FileUsageTracker(TYPOFIXER_LOG_FILE)
    elif not DIRECTUS_TOKEN:
        warnings.warn("No DIRECTUS_TOKEN set, logging to file.")
        return FileUsageTracker(TYPOFIXER_LOG_FILE)
    elif not DIRECTUS_DOMAIN:
        warnings.warn("No DIRECTUS_URL set, logging to file.")
        return FileUsageTracker(TYPOFIXER_LOG_FILE)
    else:
        return DirectusUsageTracker(
            domain=DIRECTUS_DOMAIN,
            collection=DIRECTUS_COLLECTION,
            token=DIRECTUS_TOKEN,
        )


if __name__ == "__main__":
    the_tracker = tracker()
    if isinstance(the_tracker, DirectusUsageTracker):
        the_tracker.export_schema()
    else:
        print("Directus disabled or not configured. No schema to export.")
        exit(1)
