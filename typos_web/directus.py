# %%
import json
import os
import requests
import warnings


DIRECTUS_DOMAIN = os.getenv("DIRECTUS_DOMAIN")
DIRECTUS_COLLECTION = os.getenv("DIRECTUS_COLLECTION", "typofixer_requests")
DIRECTUS_TOKEN = os.getenv("DIRECTUS_TOKEN")
DIRECTUS_DISABLE = os.getenv("DIRECTUS_DISABLE")


def log_call(model: str, input_text: str, output_text: str, input_tokens: int, output_tokens: int):
    if DIRECTUS_DISABLE:
        return
    if not DIRECTUS_TOKEN:
        warnings.warn("No DIRECTUS_TOKEN set, not logging usage.")
        return
    if not DIRECTUS_DOMAIN:
        warnings.warn("No DIRECTUS_URL set, not logging usage.")
        return

    url = f"{DIRECTUS_DOMAIN}/items/{DIRECTUS_COLLECTION}"

    response = requests.post(
        url,
        json={
            "model": model,
            "input_length": len(input_text),
            "output_length": len(output_text),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
        },
        headers={"Authorization": f"Bearer {DIRECTUS_TOKEN}"},
    )
    response.raise_for_status()

def export_schema():
    assert DIRECTUS_DOMAIN
    assert DIRECTUS_TOKEN
    # %%
    url = f"{DIRECTUS_DOMAIN}/schema/snapshot"
    response = requests.get(url, headers={"Authorization": f"Bearer {DIRECTUS_TOKEN}"})
    response.raise_for_status()
    schema = response.json()["data"]

    # Clean up schema, to have only the fields/collections we need
    schema["collections"] = [
        c for c in schema["collections"] if c["collection"] == DIRECTUS_COLLECTION
    ]
    schema["fields"] = [
        f for f in schema["fields"] if f["collection"] == DIRECTUS_COLLECTION
    ]
    schema["relations"] = [
        r for r in schema["relations"] if r["collection"] == DIRECTUS_COLLECTION
    ]





    # %%

    print(json.dumps(schema, indent=2))

if __name__ == "__main__":
    export_schema()