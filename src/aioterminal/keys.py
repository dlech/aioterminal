import enum

from .codes import C0, CSI, SS3


class Key(enum.Enum):
    UP_ARROW = enum.auto()
    DOWN_ARROW = enum.auto()
    RIGHT_ARROW = enum.auto()
    LEFT_ARROW = enum.auto()
    BEGIN = enum.auto()
    END = enum.auto()
    HOME = enum.auto()
    INSERT = enum.auto()
    DELETE = enum.auto()
    PAGE_UP = enum.auto()
    PAGE_DOWN = enum.auto()
    F1 = enum.auto()
    F2 = enum.auto()
    F3 = enum.auto()
    F4 = enum.auto()
    F5 = enum.auto()
    F6 = enum.auto()
    F7 = enum.auto()
    F8 = enum.auto()
    F9 = enum.auto()
    F10 = enum.auto()
    F11 = enum.auto()
    F12 = enum.auto()
    F13 = enum.auto()
    F14 = enum.auto()
    F15 = enum.auto()
    F16 = enum.auto()
    F17 = enum.auto()
    F18 = enum.auto()
    F19 = enum.auto()
    F20 = enum.auto()
    TAB = enum.auto()
    ENTER = enum.auto()
    ESCAPE = enum.auto()
    SPACE = enum.auto()
    BACKSPACE = enum.auto()


def code_to_key(code: int | str | SS3 | CSI) -> Key | None:
    match code:
        case C0.CR | "\r":
            return Key.ENTER
        case C0.HT | "\t":
            return Key.TAB
        case C0.ESC | "\x1b":
            return Key.ESCAPE
        case C0.SP | " ":
            return Key.SPACE
        case C0.DEL | "\x7f":
            return Key.BACKSPACE
        case CSI("", "", "", "A"):
            return Key.UP_ARROW
        case CSI("", "", "", "B"):
            return Key.DOWN_ARROW
        case CSI("", "", "", "C"):
            return Key.RIGHT_ARROW
        case CSI("", "", "", "D"):
            return Key.LEFT_ARROW
        case CSI("", "", "", "E"):
            return Key.BEGIN
        case CSI("", "", "", "F"):
            return Key.END
        case CSI("", "", "", "H"):
            return Key.HOME
        case CSI("", "2", "", "~"):
            return Key.INSERT
        case CSI("", "3", "", "~"):
            return Key.DELETE
        case CSI("", "5", "", "~"):
            return Key.PAGE_UP
        case CSI("", "6", "", "~"):
            return Key.PAGE_DOWN
        case CSI("", "15", "", "~"):
            return Key.F5
        case CSI("", "17", "", "~"):
            return Key.F6
        case CSI("", "18", "", "~"):
            return Key.F7
        case CSI("", "19", "", "~"):
            return Key.F8
        case CSI("", "20", "", "~"):
            return Key.F9
        case CSI("", "21", "", "~"):
            return Key.F10
        case CSI("", "23", "", "~"):
            return Key.F11
        case CSI("", "24", "", "~"):
            return Key.F12
        case CSI("", "25", "", "~"):
            return Key.F13
        case CSI("", "26", "", "~"):
            return Key.F14
        case CSI("", "28", "", "~"):
            return Key.F15
        case CSI("", "20", "", "~"):
            return Key.F16
        case CSI("", "31", "", "~"):
            return Key.F17
        case CSI("", "32", "", "~"):
            return Key.F18
        case CSI("", "33", "", "~"):
            return Key.F19
        case CSI("", "34", "", "~"):
            return Key.F20
        case SS3("P"):
            return Key.F1
        case SS3("Q"):
            return Key.F2
        case SS3("R"):
            return Key.F3
        case SS3("S"):
            return Key.F4
        case _:
            return None
