import difflib
import random
from textwrap import dedent
import streamlit as st

import constants
from formatting import split_words, fmt_diff_toggles
from llm import ai_stream


def main():
    st.set_page_config(initial_sidebar_state="collapsed", page_title="LLM Typo Fixer")

    st.title("LLM Typo Fixer")

    all_hearts = "❤️-🧡-💛-💚-💙-💜-🖤-🤍-🤎-💖-❤️‍🔥".split("-")
    heart = random.choice(all_hearts)

    st.write(
    f"""
    It's simple.
    1. You input a text
    2. An LLM rewrites it
    3. You see the differences:
        :red[red text is yours], :green[green is suggestions].
    4. You click to toggle between the original and new version.
    5. Copy-Paste once you're happy!

    Made with {heart} by [Diego Dorn](https://ddorn.fr). If you find it useful, [please contribute](https://paypal.me/diegodorn), each request costs me ~1 cent.

    ---
    """)

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

    system_name = st.radio("Preset instructions for the LLM", list(system_prompts.keys()), horizontal=True)
    assert system_name is not None  # For type checker

    with st.form(key="fix"):

        # Allow for custom prompts also
        if system_name == "Custom":
            system = st.text_area("Custom prompt", value=dedent(system_prompts["Fix typos"]).strip(), max_chars=constants.MAX_CHARS)
        else:
            system = dedent(system_prompts[system_name]).strip()
            st.code(system, language="text")

        text = st.text_area("Text to fix", max_chars=constants.MAX_CHARS)

        model = st.selectbox(
            "Model", constants.MODELS, index=constants.MODELS.index(constants.CHEAP_BUT_GOOD)
        )
        assert model is not None  # For the type checker.

        lets_gooo = st.form_submit_button("Fix", type="primary")


    @st.cache_resource()
    def cache():
        return {}


    if lets_gooo:
        corrected = st.write_stream(ai_stream(system, [dict(role="user", content=text)], model=model))
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
        words1 = split_words(text)
        words2 = split_words(corrected)

        diff = list(difflib.ndiff(words1, words2))

        st.header("Corrected text")
        options = [":red[Original text]", ":green[New suggestions]"]
        selected = st.radio("Select all", options, index=1, horizontal=True)

        with st.container(border=True):
            st.html(fmt_diff_toggles(diff, start_with_old_selected=selected == options[0]))

        st.warning("This text was written by a generative AI model. You **ALWAYS** need to review it.")

        st.expander("LLM version of the text").text(corrected)


    if dev_mode:
        st.expander("Raw diff").write(diff)


if __name__ == '__main__':
    main()