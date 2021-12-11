#!/usr/bin/env python3
import argparse
import asyncio

from aiohttp.client import ClientSession
from dotenv import dotenv_values

from helpers.dl import dl
from helpers.login import login


def parse_args():
    config = dotenv_values(".env")
    MYSNU_ID = config.get("MYSNU_ID")
    MYSNU_PASSWORD = config.get("MYSNU_PASSWORD")

    parser = argparse.ArgumentParser()
    parser.add_argument("course_id", type=int)
    parser.add_argument("weeks", type=int, nargs="*")
    parser.add_argument("--my-snu-id", type=str, nargs="?", default=MYSNU_ID)
    parser.add_argument("--my-snu-pw", type=str, nargs="?", default=MYSNU_PASSWORD)
    return parser.parse_args()


async def main(course_id: int, weeks: list[int], my_snu_id: str, my_snu_pw: str):
    async with ClientSession() as session:
        await login(session, my_snu_id, my_snu_pw)
        await dl(session, course_id, weeks)


if __name__ == "__main__":
    args = vars(parse_args())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(**args))
