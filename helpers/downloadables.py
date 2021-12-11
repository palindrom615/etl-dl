import os
import re
import unicodedata
from abc import abstractmethod
from typing import Protocol

from bs4 import BeautifulSoup
from requests import Session


def norm_filepath(value) -> str:
    value = str(value)
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"[^\w\s\-_\.,\(\)/]", "_", value)


class Downloadable(Protocol):
    location = ""

    @abstractmethod
    def download(self, session: Session) -> None:
        raise NotImplementedError


class Video(Downloadable):
    id: str = ""
    location: str = ""

    def __init__(self, id: str, location: str) -> None:
        self.id = id
        self.location = norm_filepath(str(location))
        os.makedirs(self.location, exist_ok=True)

    def download(self, session: Session) -> None:
        response = session.get(
            "http://etl.snu.ac.kr/mod/vod/viewer.php",
            params={"id": self.id},
        )
        playlist = re.search(
            "(http:\/\/etlstream.snu.ac.kr:1935.*playlist\.m3u8)", response.text
        ).group(0)
        soup = BeautifulSoup(response.text, features="html.parser")
        title = soup.find("title").get_text()
        print(title)
        os.system(
            f'ffmpeg -hide_banner -loglevel error -i {playlist} -c copy "{self.location}/{norm_filepath(title)}.mp4"'
        )
        soup.decompose()


class File(Downloadable):
    url: str = ""
    location: str = ""

    def __init__(self, id: str, location: str) -> None:
        self.id = id
        self.location = norm_filepath(location)
        os.makedirs(self.location, exist_ok=True)

    def download(self, session: Session) -> None:
        response = session.get(self.url)
        filename = re.search(
            'filename="(.*)"', response.headers["Content-Disposition"]
        ).group(1)
        print(filename)
        with open(f"{self.location}/{filename}", "wb") as f:
            f.write(response.content)
