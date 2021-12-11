from aiohttp import ClientSession as Session
from bs4 import BeautifulSoup

from .downloadables import Course


async def dl(session: Session, course_id: int, weeks: list[int]):
    async with session.get(
        "http://etl.snu.ac.kr/course/view.php",
        params={"id": course_id},
    ) as res:
        content = await res.text()
    soup = BeautifulSoup(content, features="html.parser")
    course = Course.from_html(soup, weeks)
    soup.decompose()
    await course.download(session, ".site")
