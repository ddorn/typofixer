import difflib
import os
import random
from textwrap import dedent
import time
import streamlit as st

import constants
from formatting import split_words, fmt_diff_toggles
from llm import ai_stream
import usage


MAX_30_DAY_COST = float(os.getenv("MAX_30_DAY_COST", -1))


def show_metrics(tracker) -> float:
    """Show usage metrics and return the cost for the last 30 days."""
    cols = st.columns(2)

    with cols[0]:
        cost = tracker.total_cost(0)
        cost_this_month = tracker.total_cost(time.time() - 30 * 24 * 3600)
        st.metric("Total API cost", f"{cost:.02f}$", f"Last 30 days: {cost_this_month:.02f}$")

    with cols[1]:
        # Display the number of requests
        requests = tracker.requests_count(0)
        requests_this_month = tracker.requests_count(time.time() - 30 * 24 * 3600)
        st.metric("Total requests", f"{requests}", f"Last 30 days: {requests_this_month}")

    return cost_this_month


def main():
    st.set_page_config(initial_sidebar_state="expanded", page_title="LLM Typo Fixer")

    st.title("LLM Typo Fixer")

    tracker = usage.tracker()

    all_hearts = "❤️-🧡-💛-💚-💙-💜-🖤-🤍-🤎-💖-❤️‍🔥".split("-")
    heart = random.choice(all_hearts)

    with st.sidebar:
        st.write(
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

        last_30_days_cost = show_metrics(tracker)

        st.write(
            """
        ## Privacy
        Your data is sent to my server, where it is not stored and is only sent to
        OpenAI/Anthropic depending on your choice of model. I only log the size of the requests to monitor usage.
        You can also run this locally by following the instructions on the [GitHub repo](
        https://github.com/ddorn/typofixer). OpenAI and Anthropic may do many things with your data,
        including training on anonymized versions of it and storing it for 30 days.
        """
        )

    if MAX_30_DAY_COST >= 0 and (last_30_days_cost >= MAX_30_DAY_COST):
        st.warning(
            "Free credits for global use have expired. You can [set up a local instance](https://github.com/ddorn/typofixer) with your own API keys."
            " Or email typofixer@therandom.space and [make a donation](https://paypal.me/diegodorn), though I don't garanty to be fast. Sorry :s"
        )
        can_run = False
    else:
        can_run = True

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

        model = st.selectbox(
            "Model", constants.MODELS, index=constants.MODELS.index(constants.CHEAP_BUT_GOOD)
        )
        assert model is not None  # For the type checker.

        lets_gooo = st.form_submit_button("Fix", type="primary")

    @st.cache_resource()
    def cache():
        return {}

    if lets_gooo:
        if not can_run:
            st.warning("Sorry, there's no more credits!")
            st.stop()
        tokens = []  # A hack to get the value out of the function while still streaming easily.
        corrected = st.write_stream(
            ai_stream(
                system,
                [dict(role="user", content=text)],
                model=model,
                usage_callback=lambda inputs, outputs: tokens.extend([inputs, outputs]),
            )
        )
        tracker.log_call(model, text, corrected, tokens[0], tokens[1])
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

        st.warning(
            "This text was written by a generative AI model. You **ALWAYS** need to review it."
        )

        st.expander("LLM version of the text").text(corrected)

    if dev_mode:
        st.expander("Raw diff").write(diff)


if __name__ == "__main__":
    main()
