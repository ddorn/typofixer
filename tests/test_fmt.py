import pytest

from typofixer.formatting import mk_diff, pair_up_diff


@pytest.mark.parametrize(
    "initial,corrected,expected",
    [
        ("openning", "opening", ["open", ("n", ""), "ing"]),
        ("?)?", "?", ["?", (")?", "")]),
    ],
)
def test_pair_up_diff(initial, corrected, expected):
    diff = mk_diff(initial, corrected)
    out = pair_up_diff(diff)
    assert out == expected
