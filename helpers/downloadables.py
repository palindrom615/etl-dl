import asyncio
import os
import re
from abc import abstractmethod
from typing import Optional, Protocol

from aiohttp import ClientSession as Session
from aiohttp.client_reqrep import ClientResponse
from bs4 import BeautifulSoup

from helpers.utils import limit_concurrent, valid_filepath


class Downloadable(Protocol):
    @abstractmethod
    async def download(self, session: Session, location: str = "") -> None:
        raise NotImplementedError


class Video(Downloadable):
    id: str = ""
    title: str = ""

    def __init__(self, id: str, title: str) -> None:
        self.id = id
        self.title = title

    @limit_concurrent
    async def download(self, session: Session, location: str = "") -> None:
        path = valid_filepath(location, f"{self.title}.mp4")
        hls = await self._get_hls(session)
        await self._download_hls(hls, path)
        print(self.title)

    async def _download_hls(self, hls: str, dest: str) -> None:
        cmd = f'ffmpeg -hide_banner -y -loglevel error -i {hls} -c copy "{dest}"'
        proc = await asyncio.create_subprocess_shell(cmd)
        await proc.wait()

    async def _get_hls(self, session: Session) -> str:
        viewer_url = "http://etl.snu.ac.kr/mod/vod/viewer.php"
        params = {"id": self.id}
        async with session.get(viewer_url, params=params) as response:
            text = await response.text()
        hls_pattern = "(http:\/\/etlstream.snu.ac.kr:1935.*playlist\.m3u8)"
        hls = re.match(hls_pattern, text).group(0)
        return hls

    @staticmethod
    def from_html(elem: BeautifulSoup):
        id = elem.get("id").split("-")[1]
        title = elem.select_one(".instancename").contents[0]
        return Video(id, title)


class File(Downloadable):
    url: str = ""

    def __init__(self, url: str) -> None:
        self.url = url

    @limit_concurrent
    async def download(self, session: Session, location: str = "") -> None:
        async with session.get(self.url) as response:
            filename = self._get_filename(response)
            filepath = valid_filepath(location, filename)
            await self._write_to_file(response, filepath)
        print(filename)

    def _get_filename(self, res: ClientResponse):
        content_disposition = res.headers["Content-Disposition"]
        return re.search('filename="(.*)"', content_disposition).group(1)

    async def _write_to_file(self, res: ClientResponse, dest: str):
        with open(dest, "wb") as f:
            async for chunk, _ in res.content.iter_chunks():
                f.write(chunk)


class Week(Downloadable):
    title: Optional[str] = None
    videos: list[Video] = []
    files: list[File] = []

    def __init__(self, title: str, videos: list[Video], files: list[File]):
        self.title = title
        self.videos = videos
        self.files = files

    async def download(self, session: Session, location: str = "") -> None:
        location = valid_filepath(location, self.title)
        os.makedirs(location, exist_ok=True)
        downloadables = self.videos + self.files
        await asyncio.gather(*[d.download(session, location) for d in downloadables])

    @staticmethod
    def from_html(week_element: BeautifulSoup) -> "Week":
        week_num = week_element.get("id").replace("section-", "")
        week_title = week_element.get("aria-label")
        week_title = f"w{week_num}-{week_title}" if week_title else f"w{week_num}"

        vod_elements = week_element.select(".modtype_vod")
        videos = [Video.from_html(elem) for elem in vod_elements]

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
        course_name = soup.select_one(".coursename").get_text()
        week_elements = soup.select("div.total_sections li.section")
        if weeks:
            week_elements = [soup.select_one(f"li#section-{week}") for week in weeks]
        weeks = [Week.from_html(elem) for elem in week_elements]
        return Course(course_name, weeks)

    async def download(self, session: Session, location: str = ".site") -> None:
        location = valid_filepath(location, self.title)
        await asyncio.gather(*[w.download(session, location) for w in self.weeks])
