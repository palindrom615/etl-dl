import os
import re
import unicodedata

from bs4 import BeautifulSoup


def norm_filename(value) -> str:
    value = str(value)
    value = unicodedata.normalize("NFKC", value)
    return re.sub(r"[^\w\s\-_\.,\(\)]", "_", value)


def dl_week_material(session, week_element: str):
    week_element = BeautifulSoup(week_element, "html.parser")

    week_num = week_element.li.get("id").replace("section-", "")
    dirname = (
        norm_filename(f'{week_num}-{week_element.li.get("aria-label")}')
        if week_element.li.get("aria-label")
        else f"week-{week_num}"
    )
    os.makedirs(dirname)
    vod_elements = week_element.select(".modtype_vod")
    vod_ids = [vod_element.get("id").split("-")[1] for vod_element in vod_elements]
    for id in vod_ids:
        response = session.get(
            "http://etl.snu.ac.kr/mod/vod/viewer.php",
            params={"id": id},
        )
        try:
            playlist = re.search(
                "(http:\/\/etlstream.snu.ac.kr:1935.*playlist\.m3u8)", response.text
            ).group(0)
            print(playlist)
        except:
            continue
        soup = BeautifulSoup(response.text, features="html.parser")
        title = soup.find("title").get_text()
        print(title)
        os.system(
            f'ffmpeg -hide_banner -loglevel error -i {playlist} -c copy "{dirname}/{norm_filename(title)}.mp4"'
        )
        soup.decompose()

    file_elements = week_element.select(".modtype_ubfile")
    file_urls = [file_element.select_one("a")["href"] for file_element in file_elements]
    for url in file_urls:
        response = session.get(url)
        filename = f"{dirname}/" + re.search(
            'filename="(.*)"', response.headers["Content-Disposition"]
        ).group(1)
        with open(filename, "wb") as f:
            f.write(response.content)
