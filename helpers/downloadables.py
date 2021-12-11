import asyncio
import os
import re
import unicodedata
from abc import abstractmethod
from typing import Protocol

from aiohttp import ClientSession as Session
from bs4 import BeautifulSoup


def norm_filepath(value) -> str:
    value = str(value)
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"[^\w\s\-_\.,\(\)]", "_", value)


class Downloadable(Protocol):
    location = ""

    @abstractmethod
    async def download(self, session: Session) -> None:
        raise NotImplementedError


class Video(Downloadable):
    id: str = ""
    location: str = ""

    def __init__(self, id: str, location: str) -> None:
        self.id = id
        self.location = location
        os.makedirs(self.location, exist_ok=True)

    async def download(self, session: Session) -> None:
        async with session.get(
            "http://etl.snu.ac.kr/mod/vod/viewer.php",
            params={"id": self.id},
        ) as response:
            text = await response.text()
        playlist = re.search(
            "(http:\/\/etlstream.snu.ac.kr:1935.*playlist\.m3u8)", text
        ).group(0)
        soup = BeautifulSoup(text, features="html.parser")
        title = soup.find("title").get_text()
        soup.decompose()

        print(title)
        proc = await asyncio.create_subprocess_shell(
            f'ffmpeg -hide_banner -loglevel error -i {playlist} -c copy "{self.location}/{norm_filepath(title)}.mp4"'
        )
        await proc.wait()


class File(Downloadable):
    url: str = ""
    location: str = ""

    def __init__(self, url: str, location: str) -> None:
        self.url = url
        self.location = location
        os.makedirs(self.location, exist_ok=True)

    async def download(self, session: Session) -> None:
        async with session.get(self.url) as response:

            filename = re.search(
                'filename="(.*)"', response.headers["Content-Disposition"]
            ).group(1)
            print(filename)
            with open(f"{self.location}/{filename}", "wb") as f:
                async for chunk, _ in response.content.iter_chunks():
                    f.write(chunk)
