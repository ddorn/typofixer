from pathlib import Path
import random
from textwrap import dedent
import openai
from pydantic import BaseModel
import streamlit as st
import streamlit.components.v1 as components
import yaml

import constants  # Needs to be imported first, as it loads the environment variables.
from formatting import mk_diff, fmt_diff_toggles
from llm import ai_stream


def setup_analytics():
    components.html(
        """
        <script async defer src="https://umami.therandom.space/script.js" data-website-id="66045f1a-46b5-41a1-9d29-daa734b222a8"></script>
        """,
        height=0,
    )


class Config(BaseModel):
    api_base: str | None = None
    api_key: str | None = None

    @classmethod
    def load(cls) -> "Config":
        try:
            path = Path(constants.CONFIG_PATH)
            data = yaml.safe_load(path.read_text())
            return cls.model_validate(data)
        except FileNotFoundError:
            return cls()


def main():
    st.set_page_config(initial_sidebar_state="expanded", page_title="LLM Typo Fixer")

    config = Config.load()
    client = openai.OpenAI(
        api_key=config.api_key,
        base_url=config.api_base,
    )

    st.title("LLM Typo Fixer")

    all_hearts = "❤️-🧡-💛-💚-💙-💜-🖤-🤍-🤎-💖-❤️‍🔥".split("-")
    heart = random.choice(all_hearts)

    st.sidebar.write(
        f"""
        # How to use this tool?
        It's simple.
        1. You input a text
        2. An LLM rewrites it
        3. You see the differences:
            :red[red text is yours], :green[green is suggestions].
        4. You click to toggle between the original and new version.
        5. Copy-Paste once you're happy!

        Made with {heart} by [Diego Dorn](https://ddorn.fr).
        """
    )

    st.sidebar.write(
        """
        ## Privacy
        Your data is sent to my server, where it is not stored and is forwarded to
        Groq/OpenAI/Anthropic depending on your choice of model. I only log the size of the requests to monitor usage.
        You can also run this locally by following the instructions on the [GitHub repo](
        https://github.com/ddorn/typofixer). Groq claims to not store/train on/sell your data, and OpenAI/Anthropic
        do the same, but might keep it for 30 days, unless it is classified as violating their TOS, in which case
        they keep if for up to 2 years.
        """
    )

    # with st.sidebar:
    #     setup_analytics()  # Doesn't actually work

    system_prompts = {
        "Fix typos": """
            You are given a text and you need to fix the language (typos, grammar, ...).
            If needed, fix the formatting and, when relevant, ensure the text is inclusive.
            Output directly the corrected text, without any comment.
            """,
        "Heavy fix": """
            You are given a text and you need to fix the language (typos, grammar, ...).
            If needed, fix the formatting and, when relevant, ensure the text is inclusive.
            Please also reformulate the text when needed, use better words and make it more clear.
            Output directly the corrected text, without any comment.
            """,
        "Custom": "",
    }

    system_name = st.radio(
        "Preset instructions for the LLM", list(system_prompts.keys()), horizontal=True
    )
    assert system_name is not None  # For type checker

    with st.form(key="fix"):

        # Allow for custom prompts also
        if system_name == "Custom":
            system = st.text_area(
                "Custom prompt",
                value=dedent(system_prompts["Fix typos"]).strip(),
                max_chars=constants.MAX_CHARS,
            )
        else:
            system = dedent(system_prompts[system_name]).strip()
            st.code(system, language="text")

        text = st.text_area("Text to fix", max_chars=constants.MAX_CHARS)

        models = client.models.list()
        model_names = [model.id for model in models.data]
        model = st.selectbox(
            "Model",
            model_names,
        )
        assert model is not None  # For the type checker.

        lets_gooo = st.form_submit_button("Fix", type="primary")

    @st.cache_resource()
    def cache():
        return {}

    if lets_gooo:
        corrected = st.write_stream(
            ai_stream(
                system,
                [dict(role="user", content=text)],
                model=model,
                client=client,
            )
        )
        cache()[text, system] = corrected
        st.rerun()
    else:
        corrected = cache().get((text, system))

    dev_mode = st.sidebar.toggle("Developer mode")
    if dev_mode:
        text = st.text_area("Text to fix", text, height=400)
        corrected = st.text_area("Corrected text", corrected, height=400)
        st.write(corrected)

    if corrected is not None:
        # Compute the difference between the two texts
        diff = mk_diff(text, corrected)

        st.header("Corrected text")
        options = [":red[Original text]", ":green[New suggestions]"]
        selected = st.radio("Select all", options, index=1, horizontal=True)

        with st.container(border=True):
            st.html(fmt_diff_toggles(diff, start_with_old_selected=selected == options[0]))

        st.warning(
            "This text was written by a generative AI model. You **ALWAYS** need to review it."
        )

        st.expander("LLM version of the text").text(corrected)
    else:
        diff = "No diff yet"

    if dev_mode:
        st.expander("Raw diff").write(diff)


if __name__ == "__main__":
    main()
