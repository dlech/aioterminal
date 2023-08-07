import pytest

from aioterminal.codes import CSI, SS3
from aioterminal.keys import Key, code_to_key


@pytest.mark.parametrize(
    "code,key",
    [
        ("\t", Key.TAB),
        ("\r", Key.ENTER),
        ("\x1b", Key.ESCAPE),
        ("\x7f", Key.BACKSPACE),
        (" ", Key.SPACE),
        (CSI(final="A"), Key.UP_ARROW),
        (CSI(final="B"), Key.DOWN_ARROW),
        (CSI(final="C"), Key.RIGHT_ARROW),
        (CSI(final="D"), Key.LEFT_ARROW),
        (CSI(final="E"), Key.BEGIN),
        (CSI(final="H"), Key.HOME),
        (CSI(final="F"), Key.END),
        (CSI(params="1", final="~"), Key.HOME),
        (CSI(params="2", final="~"), Key.INSERT),
        (CSI(params="3", final="~"), Key.DELETE),
        (CSI(params="4", final="~"), Key.END),
        (CSI(params="5", final="~"), Key.PAGE_UP),
        (CSI(params="6", final="~"), Key.PAGE_DOWN),
        (CSI(params="15", final="~"), Key.F5),
        (CSI(params="17", final="~"), Key.F6),
        (CSI(params="18", final="~"), Key.F7),
        (CSI(params="19", final="~"), Key.F8),
        (CSI(params="20", final="~"), Key.F9),
        (CSI(params="21", final="~"), Key.F10),
        (CSI(params="23", final="~"), Key.F11),
        (CSI(params="24", final="~"), Key.F12),
        (CSI(params="25", final="~"), Key.F13),
        (CSI(params="26", final="~"), Key.F14),
        (CSI(params="28", final="~"), Key.F15),
        (CSI(params="29", final="~"), Key.F16),
        (CSI(params="31", final="~"), Key.F17),
        (CSI(params="32", final="~"), Key.F18),
        (CSI(params="33", final="~"), Key.F19),
        (CSI(params="34", final="~"), Key.F20),
        (SS3(" "), Key.SPACE),
        (SS3("I"), Key.TAB),
        (SS3("M"), Key.ENTER),
        (SS3("A"), Key.UP_ARROW),
        (SS3("B"), Key.DOWN_ARROW),
        (SS3("C"), Key.RIGHT_ARROW),
        (SS3("D"), Key.LEFT_ARROW),
        (SS3("H"), Key.HOME),
        (SS3("F"), Key.END),
        (SS3("P"), Key.F1),
        (SS3("Q"), Key.F2),
        (SS3("R"), Key.F3),
        (SS3("S"), Key.F4),
        # most printable characters don't currently have a key
        ("a", None),
    ],
)
def test_code_to_key(code, key):
    assert code_to_key(code) == key
