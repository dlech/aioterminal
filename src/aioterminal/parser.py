from __future__ import annotations

import asyncio
import dataclasses
import itertools
import typing

from .codes import CSI, SS2, SS3

# state machine based on info from https://www.vt100.net/emu/dec_ansi_parser


class Action:
    @staticmethod
    def ignore(code: int, context: _Context):
        pass

    @staticmethod
    def print(code: int, context: _Context):
        if context.single_shift == 2:
            context.single_shift = 0
            return SS2(chr(code))

        if context.single_shift == 3:
            context.single_shift = 0
            return SS3(chr(code))

        return chr(code)

    @staticmethod
    def execute(code: int, context: _Context):
        ...

    @staticmethod
    def clear(context: _Context):
        context.private_markers.clear()
        context.intermediate_chars.clear()
        context.final_char = None
        context.params.clear()
        context.single_shift = 0

    @staticmethod
    def collect(code: int, context: _Context):
        if 0x20 <= code <= 0x2F:
            context.intermediate_chars.append(code)
        elif code == 0x3A or 0x3C <= code <= 0x3F:
            context.private_markers.append(code)
        else:
            assert False

    @staticmethod
    def param(code: int, context: _Context):
        assert 0x30 <= code <= 0x39 or code == 0x3B
        context.params.append(code)

    @staticmethod
    def esc_dispatch(code: int, context: _Context):
        if code == 0x4E:  # 'N'
            context.single_shift = 2
            return

        if code == 0x4F:  # 'O'
            context.single_shift = 3
            return

        ...

    @staticmethod
    def csi_dispatch(code: int, context: _Context):
        assert len(context.intermediate_chars) <= 2

        return CSI(
            "".join(chr(c) for c in context.private_markers),
            "".join(chr(c) for c in context.params),
            "".join(chr(c) for c in context.intermediate_chars),
            chr(code),
        )

    @staticmethod
    def hook(context: _Context):
        ...

    @staticmethod
    def put(code: int, context: _Context):
        ...

    @staticmethod
    def unhook(context: _Context):
        ...

    @staticmethod
    def osc_start(context: _Context):
        ...

    @staticmethod
    def osc_put(code: int, context: _Context):
        ...

    @staticmethod
    def osc_end(context: _Context):
        ...


_ENTRY_ATTR = "entry"
_EXIT_ATTR = "exit"


def _entry(action):
    def decorator(target):
        setattr(target, _ENTRY_ATTR, action)
        return target

    return decorator


def _exit(action):
    def decorator(target):
        setattr(target, _EXIT_ATTR, action)
        return target

    return decorator


class State:
    @staticmethod
    def ground(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.print(code, context)

        if 0x20 <= code <= 0x7F or code > 0xFF:  # SP to '~' or unicode
            return Action.print(code, context)

    @staticmethod
    @_entry(Action.clear)
    def escape(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.execute(code, context)

        if 0x20 <= code <= 0x2F:  # SP to '/'
            ret = Action.collect(code, context)
            _change_state(State.escape_intermediate, context)
            return ret

        if code == 0x50:  # 'P'
            _change_state(State.dcs_entry, context)
            return

        if code == 0x58 or code == 0x5E or code == 0x5F:  # 'X', '^', '_'
            _change_state(State.sos_pm_apc_string, context)
            return

        if code == 0x5B:  # '['
            _change_state(State.csi_entry, context)
            return

        if code == 0x5D:  # ']'
            _change_state(State.osc_string, context)
            return

        if 0x30 <= code <= 0x7E:  # '0' to '~'
            # these should handled above
            assert code != 0x50  # 'P'
            assert code != 0x58  # 'X'
            assert code != 0x5B  # '['
            assert code != 0x5D  # ]'
            assert code != 0x5E  # '^'
            assert code != 0x5F  # '_'

            ret = Action.esc_dispatch(code, context)
            _change_state(State.ground, context)
            return ret

        if code == 0x7F:  # DEL
            return Action.ignore(code, context)

    @staticmethod
    def escape_intermediate(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.execute(code, context)

        if 0x20 <= code <= 0x2F:  # SP to '/'
            ret = Action.collect(code, context)
            _change_state(State.csi_intermediate, context)
            return ret

        if 0x30 <= code <= 0x7E:  # '0' to '~'
            return Action.esc_dispatch(code, context)

        if code == 0x7F:  # DEL
            return Action.ignore(code, context)

    @staticmethod
    @_entry(Action.clear)
    def csi_entry(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.execute(code, context)

        if 0x20 <= code <= 0x2F:  # SP to '/'
            ret = Action.collect(code, context)
            _change_state(State.csi_intermediate, context)
            return ret

        if code == 0x3A:  # ':'
            _change_state(State.csi_ignore, context)
            return

        if 0x30 <= code <= 0x3F:  # '0' to '?'
            # handled above
            assert code != 0x3A  # ':'

            if code < 0x3C:  # '0' to '9', ';'
                ret = Action.param(code, context)
            else:
                ret = Action.collect(code, context)

            _change_state(State.csi_param, context)
            return ret

        if 0x40 <= code <= 0x7E:  # '@' to '~'
            ret = Action.csi_dispatch(code, context)
            _change_state(State.ground, context)
            return ret

        if code == 0x7F:  # DEL
            return Action.ignore(code, context)

    @staticmethod
    def csi_param(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.execute(code, context)

        if 0x20 <= code <= 0x2F:  # SP to '/'
            ret = Action.collect(code, context)
            _change_state(State.csi_intermediate, context)
            return ret

        if 0x30 <= code <= 0x39 or code == 0x3B:  # '0' to '9', ';'
            return Action.param(code, context)

        if code == 0x3A or 0x3C <= code <= 0x3F:  # ':', '<' to '?'
            _change_state(State.csi_ignore, context)
            return

        if 0x40 <= code <= 0x7E:  # '@' to '~'
            ret = Action.csi_dispatch(code, context)
            _change_state(State.ground, context)
            return ret

        if code == 0x7F:  # DEL
            return Action.ignore(code, context)

    @staticmethod
    def csi_intermediate(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.execute(code, context)

        if 0x20 <= code <= 0x2F:  # SP to '/'
            ret = Action.collect(code, context)
            _change_state(State.csi_intermediate, context)
            return ret

        if 0x30 <= code <= 0x3F:  # '0' to '?'
            _change_state(State.csi_ignore, context)
            return

        if 0x40 <= code <= 0x7E:  # '@' to '~'
            ret = Action.csi_dispatch(code, context)
            _change_state(State.ground, context)
            return ret

        if code == 0x7F:  # DEL
            return Action.ignore(code, context)

    @staticmethod
    def csi_ignore(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.execute(code, context)

        if 0x20 <= code <= 0x3F or code == 0x7F:  # SP to '?', DEL
            return Action.ignore(code, context)

        if 0x40 < -code <= 0x7E:  # '@' to '~'
            _change_state(State.ground, context)
            return

    @staticmethod
    @_entry(Action.clear)
    def dcs_entry(code: int, context: _Context):
        if 0x00 <= code <= 0x1F or code == 0x7F:
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.ignore(code, context)

        if 0x20 <= code <= 0x2F:  # SP to '/'
            ret = Action.collect(code, context)
            _change_state(State.dcs_intermediate, context)
            return ret

        if code == 0x3A:  # ':'
            _change_state(State.dcs_ignore, context)
            return

        if 0x30 <= code <= 0x3F:  # '0' to '?'
            # handled above
            assert code != 0x3A  # ':'

            if code < 0x3C:  # '0' to '9', ';'
                ret = Action.param(code, context)
            else:
                ret = Action.collect(code, context)

            _change_state(State.dcs_param, context)
            return ret

        if 0x40 <= code <= 0x7E:  # letters (and a few symbols)
            _change_state(State.dcs_passthrough, context)
            return

    @staticmethod
    def dcs_param(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.ignore(code, context)

        if 0x20 <= code <= 0x2F:  # SP to '/'
            ret = Action.collect(code, context)
            _change_state(State.dcs_intermediate, context)
            return ret

        if 0x30 <= code <= 0x39 or code == 0x3B:  # '0' to '9', ';'
            return Action.param(code, context)

        if code == 0x3A or 0x3C <= code <= 0x3F:  # ':', '<' to '?'
            _change_state(State.dcs_ignore, context)
            return

        if 0x40 <= code <= 0x7E:  # '@' to '~'
            _change_state(State.dcs_passthrough, context)
            return

        if code == 0x7F:  # DEL
            return Action.ignore(code, context)

    @staticmethod
    def dcs_intermediate(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.execute(code, context)

        if 0x20 <= code <= 0x2F:  # SP to '/'
            ret = Action.collect(code, context)
            _change_state(State.csi_intermediate, context)
            return ret

        if 0x30 <= code <= 0x3F:  # '0' to '?'
            _change_state(State.csi_ignore, context)
            return

        if 0x40 <= code <= 0x7E:  # '@' to '~'
            ret = Action.csi_dispatch(code, context)
            _change_state(State.ground, context)
            return ret

        if code == 0x7F:  # DEL
            return Action.ignore(code, context)

    @staticmethod
    @_entry(Action.hook)
    @_exit(Action.unhook)
    def dcs_passthrough(code: int, context: _Context):
        if 0x00 <= code <= 0x7E:  # NULL to '~'
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.put(code, context)

        if code == 0x7F:  # DEL
            return Action.ignore(code, context)

        if code == 0x9C:  # ST
            _change_state(State.ground, context)
            return

    @staticmethod
    def dcs_ignore(code: int, context: _Context):
        if 0x00 <= code <= 0x7F:  # NULL to '~'
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.ignore(code, context)

    @staticmethod
    @_entry(Action.osc_start)
    @_exit(Action.osc_end)
    def osc_string(code: int, context: _Context):
        if 0x00 <= code <= 0x1F:  # NULL to US
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.ignore(code, context)

        if 0x20 <= code <= 0x7F:  # SP to '~'
            return Action.osc_put(code, context)

        if code == 0x9C:  # ST
            _change_state(State.ground, context)
            return

    @staticmethod
    def sos_pm_apc_string(code: int, context: _Context):
        if 0x00 <= code <= 0x7F:  # NULL to '~'
            # these should be caught by _ANYWHERE and never reach here
            assert code != 0x18  # CAN
            assert code != 0x1A  # SUB
            assert code != 0x1B  # ESC

            return Action.ignore(code, context)

        if code == 0x9C:  # ST
            _change_state(State.ground, context)
            return


_ANYWHERE: dict[int, tuple[callable, callable]] = {}
_ANYWHERE.update(
    {
        k: (Action.execute, State.ground)
        for k in itertools.chain(
            [0x18, 0x1A],  # CAN, SUB
            [
                c for c in range(0x80, 0x9B) if c not in [0x90, 0x98]
            ],  # C1 control chars except DCS, SOS
        )
    }
)
_ANYWHERE[0x9C] = (Action.ignore, State.ground)  # ST
_ANYWHERE[0x1B] = (Action.ignore, State.escape)  # ESC
_ANYWHERE[0x9B] = (Action.ignore, State.csi_entry)  # CSI
_ANYWHERE[0x90] = (Action.ignore, State.dcs_entry)  # DCS
_ANYWHERE[0x9D] = (Action.ignore, State.osc_string)  # OSC
_ANYWHERE.update(
    {
        k: (Action.ignore, State.sos_pm_apc_string) for k in [0x98, 0x9E, 0x9F]
    }  # SOS, PM, APC
)


@dataclasses.dataclass
class _Context:
    state: callable[[int, typing.Self], str | None] = dataclasses.field(
        default=State.ground
    )
    private_markers: list[int] = dataclasses.field(default_factory=list)
    intermediate_chars: list[int] = dataclasses.field(default_factory=list)
    final_char: int | None = dataclasses.field(default=None)
    params: list[int] = dataclasses.field(default_factory=list)
    single_shift: int = dataclasses.field(default=0)


def _change_state(new_state, context: _Context):
    old_state = context.state

    on_exit = getattr(old_state, _EXIT_ATTR, None)

    if on_exit:
        on_exit(context)

    on_enter = getattr(new_state, _ENTRY_ATTR, None)

    if on_enter:
        on_enter(context)

    context.state = new_state


async def parse(
    stream: typing.AsyncIterator[str], escape_timeout: float = 1
) -> typing.AsyncGenerator[str, typing.Any]:
    context = _Context()
    i = aiter(stream)

    while True:
        try:
            # special case for escape key
            if context.state == State.escape:
                try:
                    # If escape char is not followed by another char
                    # before timeout.
                    task = asyncio.create_task(anext(i))
                    c = await asyncio.wait_for(asyncio.shield(task), escape_timeout)
                except asyncio.CancelledError:
                    # since the task was shielded from the timeout, only
                    # the timeout was canceled and we need to cancel the
                    # inner task as well if this coro was canceled
                    task.cancel()
                    raise
                except StopAsyncIteration:
                    # escape was the last item in the iter so need to
                    # be emitted before stopping the parser generator
                    yield "\x1b"
                    raise
                except asyncio.TimeoutError:
                    # waiting for another item after escape timed out
                    # reset to ground state and emit the char then keep
                    # waiting for the next char
                    _change_state(State.ground, context)
                    yield "\x1b"
                    c = await task
            else:
                c = await anext(i)
        except StopAsyncIteration:
            return

        code = ord(c)

        try:
            action, state = _ANYWHERE[code]
        except KeyError:
            emit = context.state(code, context)
        else:
            emit = action(code, context)
            _change_state(state, context)

        if emit is not None:
            yield emit
