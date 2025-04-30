import difflib
from html import escape
import re
from textwrap import dedent
from typing import Iterator


def fmt(
    text: str,
    fg: int | tuple[int, int, int] | None = None,
    bg: int | tuple[int, int, int] | None = None,
    underline: bool = False,
) -> str:
    """Format the text with the given colors using ANSI escape codes."""

    mods = ""

    if underline:
        mods += "\033[4m"

    if fg is not None:
        if isinstance(fg, int):
            mods += f"\033[38;5;{fg}m"
        else:
            mods += f"\033[38;2;{fg[0]};{fg[1]};{fg[2]}m"

    if bg is not None:
        if isinstance(bg, int):
            mods += f"\033[48;5;{bg}m"
        else:
            mods += f"\033[48;2;{bg[0]};{bg[1]};{bg[2]}m"

    if mods:
        text = mods + text + "\033[0m"

    return text


def fmt_diff(diff: Iterator[str]) -> tuple[str, str]:
    """Format the output of difflib.ndiff with ANSI escape codes.

    Returns:
        tuple[str, str]: The two strings (past, new) with the differences highlighted in ANSI colors.
    """

    past = ""
    new = ""
    for line in diff:
        mark = line[0]
        line = line[2:]
        match mark:
            case " ":
                past += line
                new += line
            case "-":
                past += fmt(line, fg=1, underline=True)
            case "+":
                new += fmt(line, fg=2, underline=True)
            case "?":
                pass

    return past, new


def common_prefix(str1, str2):
    min_length = min(len(str1), len(str2))
    for i in range(min_length):
        if str1[i] != str2[i]:
            return str1[:i]
    return str1[:min_length]


def common_suffix(str1, str2):
    min_length = min(len(str1), len(str2))
    if min_length == 0:
        return ""
    for i in range(1, min_length + 1):
        if str1[-i] != str2[-i]:
            return str1[-i + 1 :] if i > 1 else ""
    return str1[-min_length:]


def split_words(text: str) -> list[str]:
    # Split on newlines, while keeping them
    parts = re.findall(r"(\n+|[^\n]+)", text.strip())
    # Split on tokens, i.e. space followed by non-space
    parts = [word for part in parts for word in re.findall(r"^\S+|\s+\S+|\s+$", part)]
    # Split on punctuation
    parts = [word for part in parts for word in re.findall(r"[\w\s]+|[^\w\s]+", part)]
    return parts


def mk_diff(original: str, corrected: str) -> list[str]:
    """Compute the diff between the words in each text, using difflib."""
    words1 = split_words(original)
    words2 = split_words(corrected)

    diff = list(difflib.ndiff(words1, words2))
    return diff


def pair_up_diff(diff) -> list[str | tuple[str, str]]:

    # Diff always outputs "- old" then "+ new" word, but both can be empty
    parts: list[str | tuple[str, str]] = []

    for word in diff:
        kind = word[0]
        word = word[2:]

        if kind == " ":
            if parts and isinstance(parts[-1], str):
                parts[-1] += word
            else:
                parts.append(word)
        elif kind == "?":
            continue
        elif kind == "-":
            if parts and isinstance(parts[-1], tuple):
                parts[-1] = (parts[-1][0] + word, parts[-1][1])
            else:
                parts.append((word, ""))
        elif kind == "+":
            if parts and isinstance(parts[-1], tuple):
                parts[-1] = (parts[-1][0], parts[-1][1] + word)
            else:
                parts.append(("", word))
        else:
            raise ValueError(f"Unknown kind: {kind}")

    # Simplify the diff by cleaning (old, new) that start or end with a common substring
    new_parts = []
    for part in parts:
        if isinstance(part, tuple):
            old, new = part

            prefix = common_prefix(old, new)
            # Important, otherwise the suffix and prefix might overlap.
            if prefix:
                old = old[len(prefix) :]
                new = new[len(prefix) :]
                new_parts.append(prefix)

            suffix = common_suffix(old, new)
            if suffix:
                old = old[: -len(suffix)]
                new = new[: -len(suffix)]

            new_parts.append((old, new))
            if suffix:
                new_parts.append(suffix)
        else:
            new_parts.append(part)

    return new_parts


def fmt_diff_toggles(diff: list[str], start_with_old_selected: bool = False) -> str:
    parts = pair_up_diff(diff)

    style = (
        dedent(
            """
    <style>
        .swaper:checked + label INITIAL_SELECTED {
            user-select: none;
            color: gray;
            border-style: dashed;
            border-color: gray;
        }
        .swaper:not(:checked) + label INITIAL_NOT_SELECTED {
            user-select: none;
            color: gray;
            border-style: dashed;
            border-color: gray;
        }
        .swapable {
            padding: 2px;
            white-space: pre;
            border: 1px solid;
        }
        .swapable:first-child {
            border-top-left-radius: 5px;
            border-bottom-left-radius: 5px;
        }
        .swapable:last-child {
            border-top-right-radius: 5px;
            border-bottom-right-radius: 5px;
        }
        .original {
            border-color: red;
            background-color: rgba(255, 0, 0, 0.05);
            text-decoration-color: red;
        }
        .new {
            border-color: green;
            background-color: rgba(0, 255, 0, 0.05);
            text-decoration-color: green;
        }

        .swapable-label {
            display: inline;
        }
        .whitespace-hint {
            user-select: none;
            color: gray;
        }
        .diff {
            white-space: pre-wrap;
        }
    </style>"""
        )
        .replace("INITIAL_SELECTED", ".original" if start_with_old_selected else ".new")
        .replace("INITIAL_NOT_SELECTED", ".new" if start_with_old_selected else ".original")
        .strip()
    )

    template = """<input type="checkbox" style="display: none;" class="swaper" id={id}>\
<label for={id} class="swapable-label">\
{spans}\
</label>"""
    span_orignal = '<span class="swapable original">{content}</span>'
    span_new = '<span class="swapable new">{content}</span>'

    def fmt_part(part: str) -> str:
        if not part:
            return '<span class="whitespace-hint">∅</span>'
        else:
            return escape(part).replace("\n", '<span class="whitespace-hint">↵</span><br>')

    colored = ""
    for i, part in enumerate(parts):
        if isinstance(part, tuple):
            spans = []
            if part[0]:
                spans.append(span_orignal.format(content=fmt_part(part[0])))
            if part[1]:
                spans.append(span_new.format(content=fmt_part(part[1])))
            spans = "".join(spans)
            colored += template.format(id=i, spans=spans)
        else:
            colored += f"<span>{escape(part)}</span>"

    return f'<p class="diff">{style}{colored}</p>'
