#!/usr/bin/env python3
import argparse
import asyncio

from aiohttp.client import ClientSession
from bs4 import BeautifulSoup
from dotenv import dotenv_values

from helpers.downloadables import Course
from helpers.utils import REQ_HEADERS


async def login(session: ClientSession, id: str, pw: str) -> None:
    await session.get("http://etl.snu.ac.kr/")
    async with session.post(
        "https://sso.snu.ac.kr/safeidentity/modules/auth_idpwd",
        data={
            "si_id": id,
            "si_pwd": pw,
            "si_redirect_address": "https://sso.snu.ac.kr/snu/ssologin_proc.jsp?si_redirect_address=http://etl.snu.ac.kr/",
        },
        allow_redirects=False,
    ) as res:
        if res.headers.get("Location") and "error" in res.headers.get("Location"):
            raise ValueError("Login Failed!")
        content = await res.text()
    body = BeautifulSoup(content, "html.parser")
    data = {}
    for input in body.select("input"):
        data[input["name"]] = input["value"]
    body.decompose()
    await session.post(
        "https://sso.snu.ac.kr/nls3/fcs",
        data=data,
    )


async def download(session: ClientSession, course_id: int, weeks: list[int]):
    async with session.get(
        "http://etl.snu.ac.kr/course/view.php", params={"id": course_id}
    ) as res:
        content = await res.text()
    soup = BeautifulSoup(content, features="html.parser")
    course = Course.from_html(soup, weeks)
    soup.decompose()
    await course.download(session, ".site")


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
    async with ClientSession(headers=REQ_HEADERS) as session:
        await login(session, my_snu_id, my_snu_pw)
        await download(session, course_id, weeks)


if __name__ == "__main__":
    args = vars(parse_args())
    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(**args))
