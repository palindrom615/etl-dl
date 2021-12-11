import asyncio
import os
import re
import unicodedata
from abc import abstractmethod
from typing import Optional, Protocol

from aiohttp import ClientSession as Session
from bs4 import BeautifulSoup


def norm_filepath(value) -> str:
    value = str(value)
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"[^\w\s\-_\.,\(\)]", "_", value)


semaphore = asyncio.Semaphore(8)


async def gather(*tasks):
    async def sem_task(task):
        async with semaphore:
            return await task

    return await asyncio.gather(*(sem_task(task) for task in tasks))


class Downloadable(Protocol):
    @abstractmethod
    async def download(self, session: Session, location: str = "") -> None:
        raise NotImplementedError


class Video(Downloadable):
    id: str = ""

    def __init__(self, id: str) -> None:
        self.id = id

    async def download(self, session: Session, location: str = "") -> None:
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
        title = norm_filepath(title)
        soup.decompose()

        proc = await asyncio.create_subprocess_shell(
            f'ffmpeg -hide_banner -y -loglevel error -i {playlist} -c copy "{location}/{title}.mp4"'
        )
        await proc.wait()
        print(title)


class File(Downloadable):
    url: str = ""

    def __init__(self, url: str) -> None:
        self.url = url

    async def download(self, session: Session, location: str = "") -> None:
        async with session.get(self.url) as response:
            filename = re.search(
                'filename="(.*)"', response.headers["Content-Disposition"]
            ).group(1)
            filename = norm_filepath(filename)
            with open(f"{location}/{filename}", "wb") as f:
                async for chunk, _ in response.content.iter_chunks():
                    f.write(chunk)
        print(filename)


class Week(Downloadable):
    title: Optional[str] = None
    videos: list[Video] = []
    files: list[File] = []

    def __init__(self, title: str, videos: list[Video], files: list[File]):
        self.title = title
        self.videos = videos
        self.files = files

    async def download(self, session: Session, location: str = "") -> None:
        location = f"{location}/{self.title}"
        os.makedirs(location, exist_ok=True)
        downloadables = self.videos + self.files
        await gather(*[d.download(session, location) for d in downloadables])

    @staticmethod
    def from_html(week_element: BeautifulSoup) -> "Week":
        week_num = week_element.get("id").replace("section-", "")
        week_title = week_element.get("aria-label")
        week_title = (
            norm_filepath(f"w{week_num}-{week_title}") if week_title else f"w{week_num}"
        )
        vod_elements = week_element.select(".modtype_vod")
        vod_ids = [elem.get("id").split("-")[1] for elem in vod_elements]
        videos = [Video(id) for id in vod_ids]

        file_elements = week_element.select(".modtype_ubfile")
        file_urls = [elem.select_one("a")["href"] for elem in file_elements]
        files = [File(url) for url in file_urls]
        return Week(week_title, videos, files)


class Course(Downloadable):
    title: str = ""
    weeks: list[Week] = []

    def __init__(self, title: str, weeks: list[Week]) -> None:
        self.title = title
        self.weeks = weeks

    @staticmethod
    def from_html(soup: BeautifulSoup, weeks: list[int] = []) -> "Course":
        course_name = norm_filepath(soup.select_one(".coursename").get_text())
        if weeks:
            week_elements = [soup.select_one(f"li#section-{week}") for week in weeks]
        else:
            week_elements = soup.select("div.total_sections li.section")
        return Course(
            course_name,
            [Week.from_html(elem) for elem in week_elements],
        )

    async def download(self, session: Session, location: str = ".site") -> None:
        location = f"{location}/{self.title}"
        await asyncio.gather(*[w.download(session, location) for w in self.weeks])
