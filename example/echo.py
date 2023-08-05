import asyncio
import contextlib

from aioterminal import char_mode, read_chars
from aioterminal.keys import code_to_key
from aioterminal.parser import parse


async def main():
    with char_mode():
        print("type keys to see echo - ctrl-c to quit")
        async with contextlib.aclosing(read_chars()) as each_char:
            async for c in parse(each_char):
                print(code_to_key(c), repr(c), sep="\t")


if __name__ == "__main__":
    with contextlib.suppress(asyncio.CancelledError, KeyboardInterrupt):
        asyncio.run(main())
