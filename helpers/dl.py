import asyncio

from aiohttp import ClientSession as Session
from bs4 import BeautifulSoup

from .downloadables import File, Video, norm_filepath


class Course:
    course_name: str = ""
    videos: list[Video] = []
    files: list[File] = []

    def __init__(self, soup: BeautifulSoup, weeks: list[int] = []):
        self.course_name = soup.select_one(".coursename").get_text()
        parent_path = f".site/{self.course_name}"

        if weeks:
            week_elements = [soup.select_one(f"li#section-{week}") for week in weeks]
        else:
            week_elements = soup.select("div.total_sections li.section")

        for week_element in week_elements:
            week_num = week_element.get("id").replace("section-", "")
            week_title = week_element.get("aria-label")
            dirname = norm_filepath(
                f"{week_num}-{week_title}" if week_title else f"week-{week_num}"
            )
            location = f"{parent_path}/{dirname}"

            vod_elements = week_element.select(".modtype_vod")
            vod_ids = [
                vod_element.get("id").split("-")[1] for vod_element in vod_elements
            ]
            self.videos.extend([Video(id, location) for id in vod_ids])

            file_elements = week_element.select(".modtype_ubfile")
            file_urls = [
                file_element.select_one("a")["href"] for file_element in file_elements
            ]
            self.files.extend([File(url, location) for url in file_urls])


async def dl(session: Session, course_id: int, weeks: list[int]):

    async with session.get(
        "http://etl.snu.ac.kr/course/view.php",
        params={"id": course_id},
    ) as res:
        content = await res.text()
    soup = BeautifulSoup(content, features="html.parser")
    course = Course(soup, weeks)

    soup.decompose()
    return await asyncio.gather(
        *[d.download(session) for d in course.videos + course.files]
    )
