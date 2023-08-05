import pytest

from aioterminal import parser
from aioterminal.codes import CSI


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
        ("\x1b[1@", [(CSI.ICH(1))]),
        ("\x1b[?1J", [(CSI.DECSED(1))]),
        ("\x1b[1a", [(CSI.HPR(1))]),
    ],
)
async def test_sequences(seq, expected):
    actual = await _parse(seq)
    assert actual == expected
