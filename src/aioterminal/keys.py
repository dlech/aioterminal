import enum

from .codes import CSI, SS3


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
        case str(s):
            match s:
                case "\r":
                    return Key.ENTER
                case "\t":
                    return Key.TAB
                case "\x1b":
                    return Key.ESCAPE
                case " ":
                    return Key.SPACE
                case "\x7f":
                    return Key.BACKSPACE
                case _:
                    return None

        case CSI(private, params, intermediates, final):
            if not private and not intermediates:
                match final:
                    case "A":
                        return Key.UP_ARROW
                    case "B":
                        return Key.DOWN_ARROW
                    case "C":
                        return Key.RIGHT_ARROW
                    case "D":
                        return Key.LEFT_ARROW
                    case "E":
                        return Key.BEGIN
                    case "F":
                        return Key.END
                    case "H":
                        return Key.HOME
                    case "~":
                        match params:
                            case "1":
                                return Key.HOME
                            case "2":
                                return Key.INSERT
                            case "3":
                                return Key.DELETE
                            case "4":
                                return Key.END
                            case "5":
                                return Key.PAGE_UP
                            case "6":
                                return Key.PAGE_DOWN
                            case "15":
                                return Key.F5
                            case "17":
                                return Key.F6
                            case "18":
                                return Key.F7
                            case "19":
                                return Key.F8
                            case "20":
                                return Key.F9
                            case "21":
                                return Key.F10
                            case "23":
                                return Key.F11
                            case "24":
                                return Key.F12
                            case "25":
                                return Key.F13
                            case "26":
                                return Key.F14
                            case "28":
                                return Key.F15
                            case "29":
                                return Key.F16
                            case "31":
                                return Key.F17
                            case "32":
                                return Key.F18
                            case "33":
                                return Key.F19
                            case "34":
                                return Key.F20
                            case _:
                                return None
                    case _:
                        return None
        case SS3(char):
            match char:
                case " ":
                    return Key.SPACE

                case "A":
                    return Key.UP_ARROW
                case "B":
                    return Key.DOWN_ARROW
                case "C":
                    return Key.RIGHT_ARROW
                case "D":
                    return Key.LEFT_ARROW
                case "F":
                    return Key.END
                case "H":
                    return Key.HOME
                case "I":
                    return Key.TAB
                case "M":
                    return Key.ENTER
                case "P":
                    return Key.F1
                case "Q":
                    return Key.F2
                case "R":
                    return Key.F3
                case "S":
                    return Key.F4
                case _:
                    return None
        case _:
            return None
