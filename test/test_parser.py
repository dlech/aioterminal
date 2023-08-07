import asyncio
import pytest

from aioterminal import parser
from aioterminal.codes import CSI, SS3


async def aiter_str(s: str):
    for c in s:
        yield c


async def _parse(s: str):
    result = []

    async for x in parser.parse(aiter_str(s)):
        result.append(x)

    return result


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "seq,expected",
    [
        ("test", ["t", "e", "s", "t"]),
        ("\u1234", ["\u1234"]),
        ("\t", ["\t"]),
        ("\n", ["\n"]),
        ("\r\n", ["\r", "\n"]),
        ("\x1b", ["\x1b"]),
        ("\x1b[1@", [CSI.ICH(1)]),
        ("\x1b[?1J", [CSI.DECSED(1)]),
        ("\x1b[1a", [CSI.HPR(1)]),
        ("\x1bOP", [SS3("P")]),
    ],
)
async def test_sequences(seq, expected):
    actual = await _parse(seq)
    assert actual == expected


@pytest.mark.asyncio
async def test_escape_timeout():
    async def gen():
        yield "\x1b"
        await asyncio.sleep(0.1)
        yield "A"

    actual = []

    async for c in parser.parse(gen(), escape_timeout=0.001):
        actual.append(c)

    assert actual == ["\x1b", "A"]
